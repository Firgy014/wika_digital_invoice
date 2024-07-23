from odoo import models, fields, api

class SAPAccountMoveJournal(models.Model):
    _name = 'wika.account.move.journal.sap'
    
    invoice_id = fields.Many2one('account.move', string='Invoice')
    doc_number = fields.Char(string='Doc Number')
    amount = fields.Float(string='Amount')
    ppn = fields.Float(string='PPN')
    pph_cbasis = fields.Float(string='PPH Cash Basis')
    pph_accrual = fields.Float(string='PPH Accrual')
    line = fields.Char(string='Line')
    project_id = fields.Many2one('project.project', string='Proyek', related='invoice_id.project_id')
    branch_id = fields.Many2one('res.branch', string='Divisi', related='invoice_id.branch_id')
    partner_id = fields.Many2one('res.partner', string='Vendor', related='invoice_id.partner_id')
    po_id = fields.Many2one('purchase.order', string='Nomor PO', related='invoice_id.po_id')
    status = fields.Selection([
        ('not_req', 'Not Requested'),
        ('req_proyek', 'Requested by Proyek'),
        ('req_divisi', 'Requested by Divisi'),
        ('req_pusat', 'Requested by Pusat'),
        ('ready_to_pay', 'Ready to Pay'),
        ('paid', 'Paid')
    ], string='Status')