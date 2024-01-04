from odoo import fields, models, api

class WikaInheritedAccountMove(models.Model):
    _inherit = 'account.move'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='No BAP')
    branch_id = fields.Many2one('res.branch', string='Divisi')
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    pr_id = fields.Many2one('wika.payment.request', string='Payment Request')
    document_ids = fields.One2many('wika.invoice.document.line', 'invoice_id', string='Document')

class WikaInvoiceDocumentLine(models.Model):
    _name = 'wika.invoice.document.line'

    invoice_id = fields.Many2one('account.move', string='Account Move')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(attachment=True, store=True, string='Upload File')
    filename = fields.Char(string='File Name')
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verified', 'Verified')
    ], string='Status')