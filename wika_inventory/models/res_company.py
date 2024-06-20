from odoo import models, fields, api, _
from datetime import datetime
from collections import defaultdict
from odoo.exceptions import AccessError, ValidationError
from datetime import datetime, timedelta
import logging, json
_logger = logging.getLogger(__name__)

class PickingInherit(models.Model):
    _inherit = "res.company"

    is_company_details_empty = fields.Boolean('is_company_details_empty?')

class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    is_company_details_empty = fields.Boolean('is_company_details_empty?')