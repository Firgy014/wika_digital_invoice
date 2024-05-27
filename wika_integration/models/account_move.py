from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class AccountMoveInheritWika(models.Model):
    _inherit = 'account.move'
    
    is_generated = fields.Boolean(string='Generated to TXT File', default=False)
    year = fields.Char(string='Invoice Year')
    dp_doc = fields.Char(string='DP Doc')
    retensi_doc = fields.Char(string='Retensi Doc')
