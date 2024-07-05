from odoo import _, api, fields, tools, models

import logging, json
_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    pass