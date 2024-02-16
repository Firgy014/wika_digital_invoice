from odoo import models, api, fields

class DocumentSettingModels(models.Model):
    _name = 'wika.document.setting'
    _description = 'Document Setting'

    name = fields.Char(string='Doc Setting Name')
    model_id = fields.Many2one('ir.model', string='Menu')
    transaction_type = fields.Selection([
        ('BTL', 'BTL'),
        ('BL', 'BL'),
        ('gr', 'GR'),
        ('ses', 'SES')
    ],string='Transaction Type')