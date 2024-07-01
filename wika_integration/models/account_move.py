from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class AccountMoveInheritWika(models.Model):
    _inherit = 'account.move'
    
    is_generated = fields.Boolean(string='Generated to TXT File', default=False)
    year = fields.Char(string='Invoice Year')
    dp_doc = fields.Char(string='DP Doc')
    retensi_doc = fields.Char(string='Retensi Doc')
    sap_amount_payment = fields.Float('Amount Payment', tracking=True)
    amount_due = fields.Float('Amount Due', compute='_compute_amount_due')

    def _compute_amount_due(self):
        _logger.info("# === _compute_amount_due === #")
        for rec in self:
            total_paid = 0
            if rec.partial_request_ids:
                tot_partial_amount = sum(rec.partial_request_ids.filtered(lambda x : x.payment_state == 'paid').mapped('partial_amount'))
                residual_amount = rec.total_line - tot_partial_amount
                # residual_amount = rec.sisa_partial
            else:    
                total_paid = rec.sap_amount_payment
                residual_amount = rec.total_line - total_paid
            
            _logger.info("Total Paid %s Residual Amount %s" % (str(total_paid), str(residual_amount)))

            rec.amount_due = residual_amount
    
    def _compute_status_payment(self):
        for rec in self:
            rec._compute_amount_due()
            if rec.state != 'draft':
                if rec.amount_due <= 0:
                    rec.status_payment = 'Paid'
                else:
                    rec.status_payment = 'Not Request'
            else:
                rec.status_payment = 'Not Request'

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    pph_cash_basis = fields.Float(
        string='PPh Cash Basis',
        readonly=False,
        digits='Product Price',
    )

    @api.constrains('account_id', 'display_type')
    def _check_payable_receivable(self):
        return
        #override
        # for line in self:
            # account_type = line.account_id.account_type
            # if line.move_id.is_sale_document(include_receipts=True):
            #     if (line.display_type == 'payment_term') ^ (account_type == 'asset_receivable'):
            #         raise UserError(_("Any journal item on a receivable account must have a due date and vice versa."))
            # if line.move_id.is_purchase_document(include_receipts=True):
            #     if (line.display_type == 'payment_term') ^ (account_type == 'liability_payable'):
            #         raise UserError(_("Any journal item on a payable account must have a due date and vice versa."))