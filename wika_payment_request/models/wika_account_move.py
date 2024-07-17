from odoo import fields, models, api
from odoo.exceptions import AccessError, ValidationError
from datetime import datetime

import logging, json
_logger = logging.getLogger(__name__)

class InheritAccountMove(models.Model):
    _inherit = 'account.move'
    
    pr_id = fields.Many2one('wika.payment.request', string='Payment Request')
    partial_request_ids= fields.One2many('wika.partial.payment.request', 'invoice_id',string='Partial Payment Request')
    total_partial_pr=fields.Float(string='Total Partial Payment Request', compute='_compute_amount_pr')
    amount_sisa_pr=fields.Float(string='Sisa Partial Payment Request', compute='_compute_amount_pr')
    is_partial_pr=fields.Boolean(string='Partial Payment Request',default=False,compute='_compute_is_partial_pr')
    sisa_partial = fields.Float(string='Sisa Partial', compute='_compute_sisa_partial', default=lambda self: self.total_line, store=True)
    msg_sap = fields.Char(string='Message SAP')
    sap_amount_payment = fields.Float('Amount Payment', tracking=True, compute='_compute_sap_amount_payment', store=True)

    @api.depends('partial_request_ids','total_line','status_payment')
    def _compute_amount_pr(self):
        for x in self:
            _logger.info("# === _compute_amount_pr === #")
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

    @api.depends('partial_request_ids','partial_request_ids.sap_amount_payment')
    def _compute_sap_amount_payment(self):
        for move in self:
            _logger.info("# === _compute_sap_amount_payment === #")
            move.sap_amount_payment = sum(move.partial_request_ids.mapped('sap_amount_payment'))

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
