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
    account_berelasi_id = fields.Many2one('account.account', string='Account Berelasi')
    account_pihak_ketiga_id = fields.Many2one('account.account', string='Account Pihak Ketiga')