from odoo import models, fields, api, _

class AccountAccountInheritWika(models.Model):
    _inherit = 'account.account'

    sap_code = fields.Char(string="Kode SAP")