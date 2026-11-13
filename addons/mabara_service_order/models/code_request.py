from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MabaraCodeRequest(models.Model):
    """Fig. 3: material no codificado -> Almacen solicita creacion/actualizacion de codigo al
    Administrador del ERP -> se crea en el maestro -> se comunica la disponibilidad a Almacen."""
    _name = 'mabara.code.request'
    _description = 'Solicitud de codigo de material'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char('Numero', default='Nuevo', copy=False, readonly=True)
    description = fields.Char('Descripcion del material', required=True, tracking=True)
    short_name = fields.Char('Descripcion corta')
    uom_id = fields.Many2one('uom.uom', 'Unidad de medida', required=True)
    categ_id = fields.Many2one('product.category', 'Familia')
    origin = fields.Char('Documento de origen (OC / guia / devolucion)')
    requested_by = fields.Many2one('res.users', 'Solicitado por (Almacen)', default=lambda s: s.env.user)
    assigned_code = fields.Char('Codigo maestro asignado', tracking=True)
    product_tmpl_id = fields.Many2one('product.template', 'Material creado', readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'), ('requested', 'Solicitado al Administrador del ERP'),
        ('created', 'Codigo creado'), ('communicated', 'Disponibilidad comunicada')],
        default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('mabara.code.request') or 'Nuevo'
        return super().create(vals_list)

    def action_request(self):
        self.filtered(lambda r: r.state == 'draft').write({'state': 'requested'})
        for r in self.filtered(lambda r: r.state == 'requested'):
            r.message_post(body=_('Solicitud de creacion de codigo enviada al Administrador del ERP.'))
        return True

    def action_create_code(self):
        if not self.env.user.has_group('base.group_system'):
            raise UserError(_('Solo el Administrador del ERP puede crear o actualizar codigos del maestro.'))
        for r in self:
            if r.state != 'requested':
                raise UserError(_('La solicitud debe estar en estado "Solicitado".'))
            if not r.assigned_code:
                raise UserError(_('Ingrese el codigo maestro a asignar.'))
            if self.env['product.template'].with_context(active_test=False).search(
                    [('default_code', '=', r.assigned_code)], limit=1):
                raise UserError(_('El codigo %s ya existe en el maestro de materiales.') % r.assigned_code)
            vals = {'name': r.description, 'default_code': r.assigned_code, 'short_name': r.short_name,
                    'uom_id': r.uom_id.id, 'is_storable': True, 'sale_ok': True, 'purchase_ok': True,
                    'item_type': 'Material eléctrico'}
            if r.categ_id:
                vals['categ_id'] = r.categ_id.id
            r.product_tmpl_id = self.env['product.template'].create(vals)
            r.state = 'created'
            r.message_post(body=_('Codigo %s creado en el maestro de materiales.') % r.assigned_code)
        return True

    def action_communicate(self):
        for r in self:
            if r.state != 'created':
                raise UserError(_('Primero debe crearse el codigo.'))
            r.state = 'communicated'
            r.message_post(body=_('Disponibilidad del codigo %s comunicada a Almacen. Regrese a verificar el '
                                  'codigo en el maestro y registre el ingreso.') % r.assigned_code,
                           partner_ids=r.requested_by.partner_id.ids)
        return True
