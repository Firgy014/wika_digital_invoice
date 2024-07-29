from odoo import models, fields, api, _

class ModelName(models.Model):
    _inherit = 'res.company'

    x_api_key = fields.Char(string='X Api Key')