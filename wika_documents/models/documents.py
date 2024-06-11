from odoo import fields, api, models
import base64
from pypdf import PdfReader, PdfWriter
from io import BytesIO
from PIL import Image

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
    
    def compress_pdf(self):
        for record in self:
            # Read from bytes_stream
            reader = PdfReader(BytesIO(base64.b64decode(record.document)))
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            if reader.metadata is not None:
                writer.add_metadata(reader.metadata)
            
            # writer.remove_images()
            for page in writer.pages:
                for img in page.images:
                    _logger.info("# ==== IMAGE === #")
                    _logger.info(img.image)
                    if img.image.mode == 'RGBA':
                        png = Image.open(img.image)
                        png.load() # required for png.split()

                        new_img = Image.new("RGB", png.size, (255, 255, 255))
                        new_img.paste(png, mask=png.split()[3]) # 3 is the alpha channel
                    else:
                        new_img = img.image

                    img.replace(new_img, quality=20)
                    
            for page in writer.pages:
                page.compress_content_streams(level=9)  # This is CPU intensive!
                writer.add_page(page)

            output_stream = BytesIO()
            writer.write(output_stream)

            record.document = base64.b64encode(output_stream.getvalue())
