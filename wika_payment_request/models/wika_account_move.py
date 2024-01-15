from odoo import fields, models, api
from odoo.exceptions import AccessError, ValidationError
from datetime import datetime

class InheritAccountMove(models.Model):
    _inherit = 'account.move'
    
    pr_id = fields.Many2one('wika.payment.request', string='Payment Request')
