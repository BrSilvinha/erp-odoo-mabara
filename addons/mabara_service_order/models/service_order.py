from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MabaraServiceOrder(models.Model):
    _name = 'mabara.service.order'
    _description = 'Orden de Servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char('Numero', default='Nuevo', copy=False, readonly=True, tracking=True)
    request_date = fields.Date('Fecha de solicitud', default=fields.Date.context_today, required=True)
    partner_id = fields.Many2one('res.partner', 'Cliente / Solicitante', required=True, tracking=True)
    responsible_id = fields.Many2one('res.users', 'Responsable', default=lambda s: s.env.user, tracking=True)
    service_description = fields.Text('Descripcion del servicio', required=True)
    scheduled_date = fields.Date('Fecha programada')
    execution_date = fields.Datetime('Fecha de ejecucion', readonly=True)
    execution_notes = fields.Text('Registro de ejecucion')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    state = fields.Selection([
        ('draft', 'Solicitud'),
        ('issued', 'OS emitida'),
        ('waiting_supply', 'Por abastecer'),
        ('ready', 'Materiales reservados'),
        ('delivered', 'Materiales entregados'),
        ('executed', 'Servicio ejecutado'),
        ('closed', 'Cerrada'),
        ('cancel', 'Cancelada'),
    ], default='draft', tracking=True, copy=False)
    line_ids = fields.One2many('mabara.service.order.line', 'order_id', 'Materiales requeridos', copy=True)
    picking_ids = fields.One2many('stock.picking', 'service_order_id', 'Despachos')
    purchase_request_ids = fields.One2many('mabara.purchase.request', 'service_order_id', 'Solicitudes de compra')
    purchase_order_ids = fields.One2many('purchase.order', 'service_order_id', 'Ordenes de compra')
    picking_count = fields.Integer(compute='_compute_counts')
    request_count = fields.Integer(compute='_compute_counts')
    purchase_count = fields.Integer(compute='_compute_counts')

    @api.depends('picking_ids', 'purchase_request_ids', 'purchase_order_ids')
    def _compute_counts(self):
        for o in self:
            o.picking_count = len(o.picking_ids)
            o.request_count = len(o.purchase_request_ids)
            o.purchase_count = len(o.purchase_order_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('mabara.service.order') or 'Nuevo'
        return super().create(vals_list)

    # ---- PRO-01: solicitud -> OS emitida --------------------------------
    def action_issue(self):
        for o in self:
            if o.state != 'draft':
                continue
            if not o.line_ids:
                raise UserError(_('Registre al menos un material requerido antes de emitir la OS.'))
            o.state = 'issued'
            o.message_post(body=_('OS emitida. Requerimiento de materiales generado (%s lineas).') % len(o.line_ids))
        return True

    def _get_picking_type(self):
        return self.env.ref('mabara_service_order.picking_type_despacho_os')

    def _create_picking(self):
        self.ensure_one()
        pt = self._get_picking_type()
        has_name = 'name' in self.env['stock.move']._fields
        moves = []
        for line in self.line_ids:
            vals = {
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_id.uom_id.id,
                'location_id': pt.default_location_src_id.id,
                'location_dest_id': pt.default_location_dest_id.id,
            }
            if has_name:
                vals['name'] = line.product_id.display_name
            moves.append((0, 0, vals))
        picking = self.env['stock.picking'].create({
            'picking_type_id': pt.id,
            'location_id': pt.default_location_src_id.id,
            'location_dest_id': pt.default_location_dest_id.id,
            'origin': self.name,
            'partner_id': self.partner_id.id,
            'service_order_id': self.id,
            'move_type': 'one',
            'move_ids': moves,
        })
        picking.action_confirm()
        return picking

    def _refresh_lines(self):
        """Actualiza reservado / faltante por linea a partir del despacho."""
        for o in self:
            pickings = o.picking_ids.filtered(lambda p: p.state != 'cancel')
            done = bool(pickings) and all(p.state == 'done' for p in pickings)
            src = o._get_picking_type().default_location_src_id
            for line in o.line_ids:
                if done:
                    reserved = line.product_qty
                else:
                    mv = pickings.move_ids.filtered(lambda m: m.product_id == line.product_id)
                    reserved = min(sum(m.quantity for m in mv), line.product_qty)
                line.reserved_qty = reserved
                line.shortage_qty = max(line.product_qty - reserved, 0.0)
                free = line.product_id.with_context(location=src.id).free_qty
                line.available_qty = free + reserved

    # ---- Inventario: verificar existencias y reservar ---------------------
    def action_check_stock(self):
        for o in self:
            if o.state not in ('issued', 'waiting_supply'):
                raise UserError(_('La OS debe estar emitida para verificar existencias.'))
            picking = o.picking_ids.filtered(lambda p: p.state not in ('cancel', 'done'))[:1]
            if not picking:
                picking = o._create_picking()
            picking.action_assign()
            o._refresh_lines()
            if any(line.shortage_qty > 0 for line in o.line_ids):
                o.state = 'waiting_supply'
                o.message_post(body=_('Stock insuficiente: se requiere abastecimiento (Solicitud de Compra).'))
            else:
                o.state = 'ready'
                o.message_post(body=_('Stock suficiente: materiales reservados para la OS.'))
        return True

    def action_create_purchase_request(self):
        self.ensure_one()
        if self.state != 'waiting_supply':
            raise UserError(_('Solo se genera solicitud de compra cuando hay faltante de stock.'))
        if self.purchase_request_ids.filtered(lambda r: r.state != 'cancel'):
            raise UserError(_('Ya existe una solicitud de compra vigente para esta OS.'))
        lines = [(0, 0, {'product_id': line.product_id.id, 'product_qty': line.shortage_qty})
                 for line in self.line_ids if line.shortage_qty > 0]
        req = self.env['mabara.purchase.request'].create({
            'service_order_id': self.id, 'line_ids': lines,
            'note': _('Faltante de stock detectado en %s') % self.name})
        return req._get_records_action()

    def action_view_pickings(self):
        return self._open_related('stock.picking', self.picking_ids)

    def action_view_requests(self):
        return self._open_related('mabara.purchase.request', self.purchase_request_ids)

    def action_view_purchases(self):
        return self._open_related('purchase.order', self.purchase_order_ids)

    def _open_related(self, model, records):
        action = {'type': 'ir.actions.act_window', 'res_model': model, 'view_mode': 'list,form',
                  'domain': [('id', 'in', records.ids)], 'name': records._description}
        if len(records) == 1:
            action.update(view_mode='form', res_id=records.id)
        return action

    # ---- Ejecucion y cierre ----------------------------------------------
    def action_execute(self):
        for o in self:
            if o.state != 'delivered':
                raise UserError(_('Los materiales deben estar entregados antes de ejecutar el servicio.'))
            o.write({'state': 'executed', 'execution_date': fields.Datetime.now()})
            o.message_post(body=_('Servicio ejecutado.'))
        return True

    def action_close(self):
        for o in self:
            if o.state != 'executed':
                raise UserError(_('Solo se puede cerrar una OS con servicio ejecutado.'))
            o.state = 'closed'
            o.message_post(body=_('OS cerrada.'))
        return True

    def action_cancel(self):
        for o in self:
            if o.state in ('executed', 'closed'):
                raise UserError(_('No se puede cancelar una OS ejecutada o cerrada.'))
            o.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')).action_cancel()
            o.state = 'cancel'
        return True

    def action_reserve(self):
        """Reintenta la reserva (p. ej. tras recibir la compra)."""
        for o in self:
            if o.state != 'waiting_supply':
                raise UserError(_('Solo aplica a OS por abastecer.'))
            o.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')).action_assign()
            o._refresh_lines()
            if all(line.shortage_qty == 0 for line in o.line_ids):
                o.state = 'ready'
                o.message_post(body=_('Abastecimiento completo: materiales reservados para la OS.'))
            else:
                raise UserError(_('Aun hay faltante de stock; registre la recepcion de la compra.'))
        return True


class MabaraServiceOrderLine(models.Model):
    _name = 'mabara.service.order.line'
    _description = 'Material requerido por OS'

    order_id = fields.Many2one('mabara.service.order', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Material (maestro)', required=True,
                                 domain=[('is_storable', '=', True)])
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', string='Unidad')
    product_qty = fields.Float('Cantidad requerida', required=True, default=1.0)
    available_qty = fields.Float('Disponible al verificar', readonly=True)
    reserved_qty = fields.Float('Reservado', readonly=True)
    shortage_qty = fields.Float('Faltante', readonly=True)
