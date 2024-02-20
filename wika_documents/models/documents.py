from odoo import fields, api, models

class DocumentsDocumentInherit(models.Model):
    _inherit = "documents.document"

    purchase_id = fields.Many2one('purchase.order', string='Nomor PO')
    picking_id = fields.Many2one('stock.picking', string='Nomor GR/SES')
    invoice_id = fields.Many2one('account.move', string='No Invoice')
    is_po_doc = fields.Boolean(string='Is Purchase Orders Document')