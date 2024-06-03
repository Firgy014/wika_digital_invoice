# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import math

from lxml import etree

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import parse_date

_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None


class Currency(models.Model):
    _inherit = "res.currency"

    def round(self, amount):
        """Return ``amount`` rounded  according to ``self``'s rounding rules.

           :param float amount: the amount to round
           :return: rounded float
        """
        for rec in self:
            return tools.float_round(amount, precision_rounding=rec.rounding)
