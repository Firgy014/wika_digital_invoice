from odoo import fields, api, models

class DocumentsDocumentInherit(models.Model):
    _inherit = "documents.document"

    purchase_id = fields.Many2one('purchase.order', string='Purchase ID')
    is_po_doc = fields.Boolean(string='Is Purchase Orders Document')