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
        ('ZN01', 'ZN01 Berelasi'),
        ('ZN02', 'ZN02 Pihak Ketiga'),
        ('ZN03', 'ZN03 Internal'),
        ('ZN04', 'ZN04 KSO'),
        ('ZN05', 'ZN05 JO Non WIKA'),
        ('ZN10', 'ZN10 Customer Individu'),
        ('ZONE', 'ZONE One Time'),
        ('ZV07', 'ZV07 Kas Negara, Leasing'),
        ('ZV08', 'ZV08 Logistik Kapabeanan'),
        ('ZV09', 'ZV09 Perseorangan'),
        ('ZV11', 'ZV11 Vendor Fasilitas Bank'),
    ], string='Bill Chart of Accounts Type')
