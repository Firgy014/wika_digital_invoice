from odoo import api, fields, models, _, Command

import logging, json
_logger = logging.getLogger(__name__)


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    wika_tax_ids = fields.One2many('account.tax', 'tax_group_id', string='Wika Tax')

    