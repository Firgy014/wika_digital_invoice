from odoo import fields, models, api
from odoo.exceptions import AccessError, ValidationError
from datetime import datetime

class InheritAccountMove(models.Model):
    _inherit = 'account.move'
    
    pr_id = fields.Many2one('wika.payment.request', string='Payment Request')
    partial_request_ids= fields.One2many('wika.partial.payment.request', 'invoice_id',string='Partial Payment Request')
    total_partial_pr=fields.Float(string='Total Partial Payment Request',compute='_compute_amount_pr')
    amount_sisa_pr=fields.Float(string='Sisa Partial Payment Request',compute='_compute_amount_pr')
    is_partial_pr=fields.Boolean(string='Partial Payment Request',default=False,compute='_compute_is_partial_pr')
    status_payment = fields.Selection([
        ('Not Request', 'Not Request'),
        ('Request Proyek', 'Request Proyek'),
        ('Request Divisi', 'Request Divisi'),
        ('Request Pusat', 'Request Pusat'),
        ('Ready To Paid', 'Ready To Paid'),
        ('Paid', 'Paid')
    ], string='Payment State',default='Not Request')

    @api.depends('partial_request_ids','total_line')
    def _compute_amount_pr(self):
        for x in self:
            if x.partial_request_ids:
                x.total_partial_pr = sum(line.partial_amount for line in x.partial_request_ids if line.state == 'approved')
                x.amount_sisa_pr = x.total_line-x.total_partial_pr
            else:
                x.total_partial_pr=x.total_line
                x.amount_sisa_pr = x.total_line

    @api.depends('total_partial_pr')
    def _compute_is_partial_pr(self):
        for x in self:
            if x.partial_request_ids:
                x.is_partial_pr =True
            else:
                x.is_partial_pr=False
