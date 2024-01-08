from odoo import fields, api, models

class PickingDocument(models.Model):
    _name = "wika.picking.document.line"

    picking_id = fields.Many2one('stock.picking', string='Picking')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(string='Upload File')
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verified', 'Verified'),
    ], string='Status')

class PickingApproval(models.Model):
    _name = "wika.picking.approval.line"

    picking_id = fields.Many2one('stock.picking', string='Picking')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
    
    