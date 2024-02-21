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
        ('subkont', 'Subkon'),
        ('btl', 'BTL')
    ], string='Valuation Class')
    bill_coa_type = fields.Selection([
        ('relate', 'Berelasi'),
        ('3rd_party', 'Pihak Ketiga')
    ], string='Bill Chart of Accounts Type')
