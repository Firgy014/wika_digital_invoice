from odoo import _, api, fields, models
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    project_id = fields.Many2one('project.project', string='Project')
    divisi_id = fields.Many2one('res.branch', string='Divisi')
