# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date
from odoo.tools import frozendict

import re
from collections import defaultdict
from psycopg2 import sql


class SequenceMixin(models.AbstractModel):
    _inherit = 'sequence.mixin'

    @api.constrains(lambda self: (self._sequence_field, self._sequence_date_field))
    def _constrains_date_sequence(self):
        # bypass the constraint
        return
    