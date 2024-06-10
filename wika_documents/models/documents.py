from odoo import fields, api, models

class DocumentsDocumentInherit(models.Model):
    _inherit = "documents.document"

    purchase_id = fields.Many2one('purchase.order', string='Nomor PO', ondelete='cascade')
    picking_id = fields.Many2one('stock.picking', string='Nomor GR/SES')
    invoice_id = fields.Many2one('account.move', string='No Invoice')
    is_po_doc = fields.Boolean(string='Is Purchase Orders Document')
    invoice_id = fields.Many2one('account.move', string='No Invoice')
    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='No BAP')
    folder_id = fields.Many2one('documents.folder', string="Workspace", ondelete='set null', required=False)

    def name_get(self):
        res = []
        for document in self:
            name = document.folder_id.name if document.folder_id else ''
            name += ' > ' + document.name if document.name != '' else ''
            res.append((document.id, name))
        return res
