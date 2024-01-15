from odoo import fields, api, models

class PickingDocument(models.Model):
    _name = "wika.picking.document.line"

    picking_id = fields.Many2one('stock.picking', string='Picking')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(attachment=True, store=True, string='Upload File')
    filename = fields.Char(string='File Name')
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verified', 'Verified')
    ], string='Status')

    @api.onchange('document')
    def onchange_document_upload(self):
        if self.document:
            self.state = 'uploaded'

    @api.constrains('document', 'filename')
    def _check_attachment_format(self):
        for record in self:
            if record.filename and not record.filename.lower().endswith('.pdf'):
                raise ValidationError('Tidak dapat mengunggah file selain ekstensi PDF!')

class PickingApproval(models.Model):
    _name = "wika.picking.approval.line"

    picking_id = fields.Many2one('stock.picking', string='Picking')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
    
    