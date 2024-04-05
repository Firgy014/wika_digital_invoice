from odoo import fields, models

class AccountMoveInheritWika(models.Model):
    _inherit = 'account.move'
    
    is_generated = fields.Boolean(string='Generated to TXT File', default=False)
    year = fields.Char(string='Invoice Year')
    dp_doc = fields.Char(string='DP Doc')
