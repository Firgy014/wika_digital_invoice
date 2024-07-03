from collections import defaultdict
from datetime import timedelta
from operator import itemgetter

from odoo import _, api, Command, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet, groupby

import logging, json
_logger = logging.getLogger(__name__)

class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    pass