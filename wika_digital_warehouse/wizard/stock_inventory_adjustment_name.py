# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class StockInventoryAdjustmentName(models.TransientModel):
    _inherit = 'stock.inventory.adjustment.name'

    stock_opname_no = fields.Char('Stock Opname No.')
    stock_opname_date = fields.Date('Stock Opname Date')
