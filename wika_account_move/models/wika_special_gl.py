from odoo import models, fields

class WikaSpecialGl(models.Model):
    _name = 'wika.special.gl'
    _description = 'Wika Special GL'
    
    code = fields.Char('SG')
    name = fields.Char('Description')
    valuation_class = fields.Selection([
        ('material', 'Material'),
        ('alat', 'Alat'),
        ('upah', 'Upah'),
        ('subkont', 'Subkont'),
        ('btl', 'BTL')
    ], string='Valuation Class')
