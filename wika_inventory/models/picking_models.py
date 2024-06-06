from odoo import fields, api, models
import base64
from pypdf import PdfReader, PdfWriter
from io import BytesIO
from PIL import Image
from odoo.exceptions import AccessError, ValidationError
import logging, json
_logger = logging.getLogger(__name__)

class PickingDocument(models.Model):
    _name = "wika.picking.document.line"

    picking_id = fields.Many2one('stock.picking', string='Picking')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(attachment=True, store=True, string='Upload File')
    filename = fields.Char(string='File Name')
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], string='Status')

    @api.onchange('document')
    def onchange_document_upload(self):
        if self.document:
            if self.filename and not self.filename.lower().endswith('.pdf'):
                self.document = False
                self.filename = False
                self.state = 'waiting'
                raise ValidationError('Tidak dapat mengunggah file selain ekstensi PDF!')
            elif self.filename.lower().endswith('.pdf'):
                self.compress_pdf()
                self.state = 'uploaded'

        else:
            self.document = False
            self.filename = False
            self.state = 'waiting'

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
            # for page in writer.pages:
            #     for img in page.images:
            #         _logger.info("# ==== IMAGE === #")
            #         _logger.info(img.image)
                    # if img.image.mode == 'RGBA':
                        # rgb = Image.new('RGB', img.image.size, (255, 255, 255))
                        # continue
                        # img.image.convert('RGB')
                    # else:
                        # rgb = img.image

                    # img.replace(img.image, quality=80)
                    # _logger.info(img.image)
                    # rgb = img.image
                    
            for page in writer.pages:
                page.compress_content_streams(level=9)  # This is CPU intensive!
                writer.add_page(page)

            output_stream = BytesIO()
            writer.write(output_stream)

            record.document = base64.b64encode(output_stream.getvalue())

class PickingApproval(models.Model):
    _name = "wika.picking.approval.line"

    picking_id = fields.Many2one('stock.picking', string='Picking')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
    
    