from odoo import models, fields

class WikaSpecialGl(models.Model):
    _name = 'wika.special.gl'
    _description = 'Wika Special GL'
    
    code = fields.Char('SG')
    name = fields.Char('Description')