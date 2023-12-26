from odoo import models, api, fields

class DocumentSettingModels(models.Model):
    _name = 'wika.document.setting'

    name = fields.Char(string='Doc Setting Name')
    model_id = fields.Many2one('ir.model', string='Menu')