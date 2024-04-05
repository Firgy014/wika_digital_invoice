from odoo import fields, models, api

class SettingAccountPayable(models.Model):
    _name = 'wika.setting.account.payable'
    _description = 'Payable Account Setting'

    valuation_class = fields.Selection([
        ('material', 'Material'),
        ('alat', 'Alat'),
        ('upah', 'Upah'),
        ('subkont', 'Subkont'),
        ('btl', 'BTL')
    ], string='Product Valuation Class')
    assignment = fields.Selection([
        ('proyek', 'Proyek'),
        ('nonproyek', 'Non Proyek')
    ], string='Account Assigment')
    account_id = fields.Many2one('account.account', string='Account')
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