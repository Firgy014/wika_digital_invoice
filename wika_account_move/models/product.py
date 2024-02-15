from odoo import fields, models, api

class ProductInherit(models.Model):
    # _inherit = 'product.product'
    _inherit = 'product.template'

    valuation_class = fields.Selection([
        ('material', 'Material'),
        ('alat', 'Alat'),
        ('upah', 'Upah'),
        ('subkont', 'Subkont'),
        ('btl', 'BTL')
    ], string='Valuation Class')