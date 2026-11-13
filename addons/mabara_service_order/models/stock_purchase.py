from odoo import fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    service_order_id = fields.Many2one('mabara.service.order', 'Orden de Servicio', index=True, copy=False)
    supplier_doc = fields.Char('Documento de respaldo (OC / guia de remision)', copy=False)
    receipt_date = fields.Date('Fecha de recepcion fisica', default=fields.Date.context_today, copy=False)
    difference_note = fields.Text('Diferencias de recepcion', copy=False)

    def button_validate(self):
        # Politica 8: toda salida de materiales debe asociarse a una OS
        for p in self:
            if p.picking_type_code == 'outgoing' and p.location_dest_id.usage == 'customer' \
                    and not p.service_order_id:
                raise UserError(_('Politica 8: toda salida de materiales debe estar asociada a una '
                                  'Orden de Servicio.'))
            if p.picking_type_code == 'incoming':
                # Politica 7: la recepcion de proveedor se verifica contra la Orden de Compra
                if p.location_id.usage == 'supplier' and not getattr(p, 'purchase_id', False):
                    raise UserError(_('Politica 7: la recepcion debe verificarse contra una Orden de Compra '
                                      'antes de actualizar las existencias.'))
                # Fig. 3: el ingreso se registra el mismo dia de la recepcion
                if p.receipt_date and p.receipt_date not in (fields.Date.context_today(p), fields.Date.today()):
                    raise UserError(_('Todo ingreso debe registrarse en el ERP el mismo dia de la recepcion '
                                      '(fecha de recepcion: %s).') % p.receipt_date)
                # Fig. 3: recepcion no conforme -> registrar la diferencia y comunicar a Compras
                diffs = [m for m in p.move_ids if m.quantity and m.quantity != m.product_uom_qty]
                if diffs:
                    txt = '; '.join('%s: pedido %s, recibido %s' % (m.product_id.display_name,
                                                                    m.product_uom_qty, m.quantity)
                                    for m in diffs)
                    p.difference_note = txt
                    p.message_post(body=_('Recepcion con diferencias: %s') % txt)
                    po = getattr(p, 'purchase_id', False)
                    if po:
                        po.message_post(body=_('Comunicado a Compras - diferencias en %s: %s') % (p.name, txt))
        return super().button_validate()

    def _action_done(self):
        res = super()._action_done()
        for order in self.mapped('service_order_id'):
            pickings = order._dispatch_pickings().filtered(lambda p: p.state != 'cancel')
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
