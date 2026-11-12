from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    mabara_state = fields.Char('Estado', compute='_compute_mabara_state')

    @api.depends('active')
    def _compute_mabara_state(self):
        for t in self:
            t.mabara_state = 'Activo' if t.active else 'Archivado'
