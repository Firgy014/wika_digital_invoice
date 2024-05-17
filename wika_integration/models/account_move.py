from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class AccountMoveInheritWika(models.Model):
    _inherit = 'account.move'
    
    is_generated = fields.Boolean(string='Generated to TXT File', default=False)
    year = fields.Char(string='Invoice Year')
    dp_doc = fields.Char(string='DP Doc')
    retensi_doc = fields.Char(string='Retensi Doc')

    # @api.model_create_multi
    # def create(self, vals_list):
    #     _logger.info("DEBUGGGGG ON CREATE ACCOUNT MOVE")
    #     _logger.info(vals_list)
    #     record = super(AccountMoveInheritWika, self).create(vals_list)

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