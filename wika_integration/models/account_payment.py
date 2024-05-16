from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    line_item = fields.Char(string='Line Item')
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
