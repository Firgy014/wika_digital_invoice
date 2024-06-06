from odoo import models, fields, api

class DocApNonPO(models.Model):
    _name = 'doc.ap.non.po'
    _rec_name = "doc_number"
    
    doc_number = fields.Char(string='Doc Number')
    divisi_id = fields.Many2one('res.branch', string='Divisi', related='project_id.branch_id')
    project_id = fields.Many2one('project.project', string='Proyek')
    posting_date = fields.Date('Posting Date')
    partner_id = fields.Many2one('res.partner', string='Partner')