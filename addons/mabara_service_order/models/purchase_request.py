from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MabaraPurchaseRequest(models.Model):
    _name = 'mabara.purchase.request'
    _description = 'Solicitud de Compra'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char('Numero', default='Nuevo', copy=False, readonly=True)
    service_order_id = fields.Many2one('mabara.service.order', 'Orden de Servicio', tracking=True)
    requested_by = fields.Many2one('res.users', 'Solicitante', default=lambda s: s.env.user)
    date = fields.Date(default=fields.Date.context_today)
    note = fields.Text('Motivo')
    return_reason = fields.Text('Motivo de devolucion', tracking=True)
    state = fields.Selection([
        ('draft', 'Borrador'), ('to_approve', 'Por revisar'), ('returned', 'Devuelta para correccion'), ('approved', 'Aprobada'),
        ('rfq', 'En cotizacion'), ('cancel', 'Cancelada')], default='draft', tracking=True)
    line_ids = fields.One2many('mabara.purchase.request.line', 'request_id', 'Materiales')
    purchase_ids = fields.One2many('purchase.order', 'purchase_request_id', 'Cotizaciones / OC')
    purchase_count = fields.Integer(compute='_compute_purchase_count')

    @api.depends('purchase_ids')
    def _compute_purchase_count(self):
        for r in self:
            r.purchase_count = len(r.purchase_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('mabara.purchase.request') or 'Nuevo'
        return super().create(vals_list)

    def action_submit(self):
        for r in self:
            if not r.line_ids:
                raise UserError(_('La solicitud no tiene materiales.'))
            # Politica 4: todo requerimiento de compra nace de una necesidad registrada en el sistema
            if not r.service_order_id:
                raise UserError(_('Politica 4: la solicitud de compra debe originarse en una Orden de Servicio '
                                  'registrada.'))
            # Politica 3: Almacen verifica la disponibilidad antes de gestionar una adquisicion
            if r.service_order_id.state in ('draft', 'correction', 'issued', 'cancel'):
                raise UserError(_('Politica 3: Almacen debe verificar la disponibilidad (existencias) de la OS %s '
                                  'antes de gestionar la compra.') % r.service_order_id.name)
            r.state = 'to_approve'
        return True

    def action_return(self):
        for r in self.filtered(lambda r: r.state == 'to_approve'):
            if not r.return_reason:
                raise UserError(_('Indique el "Motivo de devolucion" para que Almacen corrija la solicitud.'))
            r.state = 'returned'
            r.message_post(body=_('Solicitud no conforme, devuelta para correccion: %s') % r.return_reason)
        return True

    def action_resubmit(self):
        for r in self.filtered(lambda r: r.state == 'returned'):
            if not r.line_ids:
                raise UserError(_('La solicitud no tiene materiales.'))
            r.state = 'to_approve'
            r.message_post(body=_('Solicitud corregida y reenviada a revision.'))
        return True

    def action_approve(self):
        self.filtered(lambda r: r.state == 'to_approve').write({'state': 'approved'})
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def action_create_rfq(self):
        """Solicita cotizacion a cada proveedor registrado en los materiales."""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('La solicitud debe estar aprobada.'))
        partners = self.line_ids.product_id.seller_ids.partner_id
        if not partners:
            raise UserError(_('Los materiales no tienen proveedores registrados.'))
        rfqs = self.env['purchase.order']
        for partner in partners:
            rfqs |= self.env['purchase.order'].create({
                'partner_id': partner.id,
                'origin': self.name,
                'purchase_request_id': self.id,
                'service_order_id': self.service_order_id.id,
                'order_line': [(0, 0, {'product_id': line.product_id.id, 'product_qty': line.product_qty})
                               for line in self.line_ids],
            })
        if 'alternative_po_ids' in rfqs._fields and len(rfqs) > 1:
            for rfq in rfqs:
                rfq.alternative_po_ids = [(6, 0, (rfqs - rfq).ids)]
        self.state = 'rfq'
        self.message_post(body=_('Cotizaciones solicitadas: %s') % ', '.join(rfqs.mapped('name')))
        return self.action_view_purchases()

    def action_view_purchases(self):
        return {'type': 'ir.actions.act_window', 'res_model': 'purchase.order', 'view_mode': 'list,form',
                'domain': [('id', 'in', self.purchase_ids.ids)], 'name': _('Cotizaciones / OC')}


class MabaraPurchaseRequestLine(models.Model):
    _name = 'mabara.purchase.request.line'
    _description = 'Linea de solicitud de compra'

    request_id = fields.Many2one('mabara.purchase.request', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Material', required=True)
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', string='Unidad')
    product_qty = fields.Float('Cantidad', required=True)
