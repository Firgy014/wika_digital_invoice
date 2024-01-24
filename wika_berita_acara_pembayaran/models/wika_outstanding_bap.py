from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
from odoo import tools

class WikaOutstandingBap(models.Model):
    _name = 'wika.outstanding.bap'
    _description = 'Wika Outstanding BAP'
    _auto = False

    purchase_id = fields.Many2one('purchase.order', string='Nomor PO')
    project_id = fields.Many2one('project.project', string='Project')
    branch_id = fields.Many2one('res.branch', string='Divisi')
    po_line = fields.Integer('PO Line')
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Integer(string='Quantity')
    currency_id = fields.Many2one('res.currency', string='Currency')
    unit_price = fields.Monetary(string='Unit Price')
    sub_total = fields.Monetary(string='Subtotal')
    picking_id = fields.Many2one('stock.move', string='NO GR/SES')
    no_gr = fields.Char(string='Nomor GR')
    qty_process = fields.Integer(string='Quantity Proses')
    no_bap = fields.Char(string='Nomor BAP')
    
    # @api.model_cr
    # def init(self):
    #     tools.drop_view_if_exists(self._cr, 'wika_berita_acara_pembayaran')
    #     self._cr.execute("""CREATE or REPLACE VIEW wika_outstanding_bap as (
    #         select id as purchase_id from purchase_order)""")
    #     # cr = self.env.cr
    #     # cr.execute("SELECT * FROM purchase_order WHERE active = true")
    #     # result = cr.fetchone()
    #     # print("BERHASILLLLLLLLLLLLLLLL")
        # print("BERHASILLLLLLLLLLLLLLLL", result)