from odoo import fields, models, api

class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    bill_coa_type = fields.Selection([
        ('relate', 'Berelasi'),
        ('3rd_party', 'Pihak Ketiga')
    ], string='Bill Chart of Accounts Type')
    # account_berelasi_id = fields.Many2one('account.account', string='Account Berelasi')
    # account_pihak_ketiga_id = fields.Many2one('account.account', string='Account Pihak Ketiga')