from odoo import fields, models, api
from odoo.exceptions import AccessError, ValidationError
from datetime import datetime

class InheritAccountMove(models.Model):
    _inherit = 'account.move'
    
    pr_id = fields.Many2one('wika.payment.request', string='Payment Request')
    partial_request_ids= fields.One2many('wika.partial.payment.request', 'invoice_id',string='Partial Payment Request')
    total_partial_pr=fields.Float(string='Total Partial Payment Request', compute='_compute_amount_pr')
    amount_sisa_pr=fields.Float(string='Sisa Partial Payment Request', compute='_compute_amount_pr')
    is_partial_pr=fields.Boolean(string='Partial Payment Request',default=False,compute='_compute_is_partial_pr')
    status_payment = fields.Selection([
        ('Not Request', 'Not Request'),
        ('Request Proyek', 'Request Proyek'),
        ('Request Divisi', 'Request Divisi'),
        ('Request Pusat', 'Request Pusat'),
        ('Ready To Pay', 'Ready To Pay'),
        ('Paid', 'Paid')
    ], string='Payment State',default='Not Request')
    sisa_partial = fields.Float(string='Sisa Partial', compute='_compute_sisa_partial', default=lambda self: self.total_line, store=True)
    
    def unlink(self):
        erorTestttt
        return super(InheritAccountMove).unlink()
    
    @api.depends('partial_request_ids','total_line','status_payment')
    def _compute_amount_pr(self):
        for x in self:
            if x.partial_request_ids and x.status_payment != 'Not Request':
                x.total_partial_pr = sum(line.partial_amount for line in x.partial_request_ids if line.state == 'approved')
                x.amount_sisa_pr = x.total_line-x.total_partial_pr
            else:
                x.total_partial_pr=x.total_line
                x.amount_sisa_pr = x.total_line

    @api.depends('partial_request_ids')
    def _compute_total_partial_pr(self):
        for move in self:
            total_line = sum(move.partial_request_ids.mapped('amount'))
            move.total_line = total_line

    @api.depends('total_line', 'partial_request_ids.partial_amount')
    def _compute_sisa_partial(self):
        for move in self:
            total_partial_amount = sum(move.partial_request_ids.mapped('partial_amount'))
            move.sisa_partial = move.total_line - total_partial_amount

    @api.depends('total_partial_pr')
    def _compute_is_partial_pr(self):
        for x in self:
            if x.partial_request_ids:
                x.is_partial_pr =True
            else:
                x.is_partial_pr=False
