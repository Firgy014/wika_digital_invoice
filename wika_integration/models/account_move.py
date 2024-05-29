from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class AccountMoveInheritWika(models.Model):
    _inherit = 'account.move'
    
    is_generated = fields.Boolean(string='Generated to TXT File', default=False)
    year = fields.Char(string='Invoice Year')
    dp_doc = fields.Char(string='DP Doc')
    retensi_doc = fields.Char(string='Retensi Doc')
    payment_move_ids = fields.One2many(
        'account.payment',
        'payment_move_id',
        string='Payments',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    amount_due = fields.Float('Amount Due')

    def _compute_amount_due(self):
        for rec in self:
            total_paid = 0
            if self.partial_request_ids:
                tot_partial_amount = sum(rec.partial_request_ids.filtered(lambda x : x.payment_state == 'paid').mapped('partial_amount'))
                residual_amount = rec.amount_total_payment - tot_partial_amount
                # residual_amount = rec.sisa_partial
            else:    
                total_paid = sum(rec.payment_move_ids.mapped('amount'))
                residual_amount = rec.amount_total_payment - total_paid
            
            _logger.info("Total Paid %s Residual Amount %s" % (str(total_paid), str(residual_amount)))

            rec.amount_due = residual_amount
    
    @api.depends('amount_residual', 'move_type', 'state', 'company_id')
    def _compute_payment_state(self):
        self._compute_amount_due();
        for rec in self:
            if rec.state != 'draft':
                if rec.amount_due == 0:
                    rec.payment_state = 'paid'
                else:
                    rec.payment_state = 'not_paid'
            else:
                rec.payment_state = 'not_paid'

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