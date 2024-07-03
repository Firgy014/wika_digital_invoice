from odoo import models, fields

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    project_id = fields.Many2one('project.project', string='Project')
    divisi_id = fields.Many2one('res.branch', string='Divisi')
