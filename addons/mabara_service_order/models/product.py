import math
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    abc_class = fields.Selection([('A', 'A'), ('B', 'B'), ('C', 'C')], 'Clasificacion ABC')
    old_codes = fields.Char('Codigos anteriores')
    short_name = fields.Char('Descripcion corta')
    item_type = fields.Char('Tipo de item')
    # Parametros OFICIALES (Tablas XI-XIII del documento)
    annual_demand = fields.Float('Demanda anual proyectada (D)')
    holding_rate = fields.Float('Tasa de mantenimiento', default=0.15)
    order_cost = fields.Float('Costo por pedido (S)')
    monthly_demand = fields.Float('Demanda mensual (d)')
    monthly_sigma = fields.Float('Desv. estandar mensual')
    lead_time_months = fields.Float('Lead time (meses)', digits=(6, 2))
    service_z = fields.Float('Z (nivel de servicio)', default=1.645, digits=(6, 3))
    eoq_official = fields.Float('EOQ (documento)')
    safety_stock_official = fields.Float('Stock de seguridad (documento)')
    reorder_point_official = fields.Float('Punto de reorden (documento)')
    # Verificacion con las formulas del documento
    holding_cost = fields.Float('H = costo x tasa', compute='_compute_policy_check', digits=(10, 3))
    eoq_check = fields.Float('EOQ recalculado', compute='_compute_policy_check')
    ss_check = fields.Float('SS recalculado', compute='_compute_policy_check')
    rop_check = fields.Float('ROP recalculado', compute='_compute_policy_check')
    lead_time_days = fields.Integer('Lead time (dias)', compute='_compute_policy_check')

    @api.depends('annual_demand', 'holding_rate', 'order_cost', 'standard_price', 'monthly_demand',
                 'monthly_sigma', 'lead_time_months', 'service_z')
    def _compute_policy_check(self):
        for t in self:
            h = t.standard_price * t.holding_rate
            t.holding_cost = h
            t.eoq_check = round(math.sqrt(2 * t.annual_demand * t.order_cost / h)) if h > 0 else 0
            ss = t.service_z * t.monthly_sigma * math.sqrt(t.lead_time_months) if t.lead_time_months > 0 else 0
            t.ss_check = round(ss)
            t.rop_check = round(t.monthly_demand * t.lead_time_months + ss)
            t.lead_time_days = round(t.lead_time_months * 30)

    def action_apply_inventory_policy(self):
        """ROP -> minimo; ROP + EOQ -> maximo; lead time -> plazo del proveedor."""
        wh = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        buy = self.env['stock.route'].search([('rule_ids.action', '=', 'buy')], limit=1)
        for t in self:
            if not (t.reorder_point_official and t.eoq_official):
                raise UserError(_('%s no tiene EOQ/ROP definidos.') % t.display_name)
            product = t.product_variant_id
            if buy:
                t.route_ids = [(4, buy.id)]
            # Odoo 19 no tiene multiplo de pedido: se pide hasta ROP + EOQ (pedido ~ EOQ al llegar al ROP)
            vals = {'product_min_qty': t.reorder_point_official,
                    'product_max_qty': t.reorder_point_official + t.eoq_official, 'trigger': 'auto'}
            op = self.env['stock.warehouse.orderpoint'].search(
                [('product_id', '=', product.id), ('warehouse_id', '=', wh.id)], limit=1)
            if op:
                op.write(vals)
            else:
                vals.update(product_id=product.id, warehouse_id=wh.id, location_id=wh.lot_stock_id.id)
                if buy:
                    vals['route_id'] = buy.id
                self.env['stock.warehouse.orderpoint'].create(vals)
            t.seller_ids.write({'delay': t.lead_time_days})
        return True
