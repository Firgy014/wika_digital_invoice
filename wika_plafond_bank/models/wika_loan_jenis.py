from odoo import fields, models
            
class WikaLoanJenis(models.Model):

    _name = 'wika.loan.jenis'  
    _rec_name = 'nama'

    nama = fields.Char(string='Nama', required="True")
    kode = fields.Char(string='Kode', required="True")
    tipe = fields.Selection(string='Tipe', selection=[
        ('Cash', 'Cash'), 
        ('Non Cash', 'Non Cash')
    ])
    account_id  = fields.Many2one(comodel_name='account.account', string="Default Account")
    lock_date = fields.Boolean(string='Lock Date')
    tipe_ids = fields.One2many(comodel_name='wika.tipe.jenis', inverse_name='jenis_id')   
    sap_code = fields.Char(string="Kode SAP")
    kelompok = fields.Selection([
        ('revolving loans', 'Revolving Loans'),
        ('terms loans', 'Terms Loans'),
    ], string='Kelompok')

class WikaTipeJenis(models.Model):

    _name = 'wika.tipe.jenis'  
    _description = 'Tipe Jenis'
    _rec_name = 'name'

    name = fields.Char(string='Nama', required="True")
    jenis_id = fields.Many2one(comodel_name='wika.loan.jenis', string='Jenis')