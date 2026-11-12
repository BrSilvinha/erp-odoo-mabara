from odoo import fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    service_order_id = fields.Many2one('mabara.service.order', 'Orden de Servicio', index=True, copy=False)

    def button_validate(self):
        # Politica 8: toda salida de materiales debe asociarse a una OS
        for p in self:
            if p.picking_type_code == 'outgoing' and p.location_dest_id.usage == 'customer' \
                    and not p.service_order_id:
                raise UserError(_('Politica 8: toda salida de materiales debe estar asociada a una '
                                  'Orden de Servicio.'))
        return super().button_validate()

    def _action_done(self):
        res = super()._action_done()
        for order in self.mapped('service_order_id'):
            pickings = order.picking_ids.filtered(lambda p: p.state != 'cancel')
            if order.state in ('ready', 'waiting_supply') and pickings \
                    and all(p.state == 'done' for p in pickings):
                order._refresh_lines()
                order.state = 'delivered'
                order.message_post(body=_('Materiales entregados y descontados del inventario.'))
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_request_id = fields.Many2one('mabara.purchase.request', 'Solicitud de compra', copy=True, index=True)
    service_order_id = fields.Many2one('mabara.service.order', 'Orden de Servicio', copy=True, index=True)

    def button_confirm(self):
        # Politicas 4 y 5: la OC nace de una solicitud (o de una regla de reabastecimiento)
        for po in self:
            from_rule = bool(po.order_line.orderpoint_id)
            if not po.purchase_request_id and not from_rule:
                raise UserError(_('Politicas 4/5: la Orden de Compra debe vincularse a una Solicitud de Compra '
                                  'o a una regla de reabastecimiento.'))
        return super().button_confirm()
