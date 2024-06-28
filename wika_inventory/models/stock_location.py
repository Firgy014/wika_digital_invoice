import calendar

from collections import defaultdict, OrderedDict
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare


class Location(models.Model):
    _inherit = "stock.location"

    project_id = fields.Many2one('project.project', string='Project')
    divisi_id = fields.Many2one('res.branch', string='Divisi')