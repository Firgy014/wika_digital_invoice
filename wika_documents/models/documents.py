from odoo import fields, api, models

class DocumentsDocumentInherit(models.Model):
    _inherit = "documents.document"

    purchase_id = fields.Many2one('purchase.order', string='Nomor PO')
    picking_id = fields.Many2one('stock.picking', string='Nomor GR/SES')
    is_po_doc = fields.Boolean(string='Is Purchase Orders Document')
    invoice_id = fields.Many2one('account.move', string='No Invoice')
    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='No BAP')
