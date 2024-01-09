from odoo import fields, models, api

class WikaInheritedAccountMove(models.Model):
    _inherit = 'account.move'
    
    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='BAP')
    branch_id = fields.Many2one('res.branch', string='Divisi')
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    pr_id = fields.Many2one('wika.payment.request', string='Payment Request')
    document_ids = fields.One2many('wika.invoice.document.line', 'invoice_id', string='Document Line')
    history_approval_ids = fields.One2many('wika.invoice.approval.line', 'invoice_id', string='History Approval Line')

class WikaInvoiceDocumentLine(models.Model):
    _name = 'wika.invoice.document.line'
    _description = 'Invoice Document Line'

    invoice_id = fields.Many2one('account.move', string='Invoice id')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(string="Upload File", attachment=True, store=True)
    filename = fields.Char(string="File Name")
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verif', 'Verif'),
    ], string='Status', default='waiting')

class WikaInvoiceApprovalLine(models.Model):
    _name = 'wika.invoice.approval.line'
    _description = 'Wika Approval Line'

    invoice_id = fields.Many2one('account.move', string='Invoice id')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')