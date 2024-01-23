from odoo import models, fields
from odoo.exceptions import UserError, ValidationError, Warning, AccessError

class WikaOutstandingBap(models.Model):
    _name = 'wika.outstanding.bap'
    _description = 'Wika Outstanding BAP'

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