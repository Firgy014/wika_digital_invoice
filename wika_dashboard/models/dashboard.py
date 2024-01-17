from odoo import models, api, fields

class DashboardDocument(models.Model):
    _name = 'wika.dashboard.document'

    name = fields.Char(string='Name')
    document_id = fields.Many2one('documents.document', string='Document')
    folder_id = fields.Many2one('documents.folder', string='Folder')
    count = fields.Integer(string="Total", compute='_compute_total_doc')

    def _compute_total_doc(self):
        for record in self:
            record.count = record.folder_id.document_count
