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