from odoo import models, fields, api

class WikaDigitalInvoicingReport(models.Model):
    _name = 'wika.digital.invoicing.report'
    _description = 'Digital Invoicing Report'

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True, default=lambda self: self.env['ir.sequence'].next_by_code('wika.digital.invoicing.report'))

    # Add fields for counts
    purchase_order_waiting_count = fields.Integer(string='Purchase Order Waiting Count', compute='_compute_purchase_order_counts')
    purchase_order_uploaded_count = fields.Integer(string='Purchase Order Uploaded Count', compute='_compute_purchase_order_counts')
    purchase_order_approved_count = fields.Integer(string='Purchase Order Approved Count', compute='_compute_purchase_order_counts')

    stock_picking_waiting_count = fields.Integer(string='Stock Picking Waiting Count', compute='_compute_stock_picking_counts')
    stock_picking_uploaded_count = fields.Integer(string='Stock Picking Uploaded Count', compute='_compute_stock_picking_counts')
    stock_picking_approved_count = fields.Integer(string='Stock Picking Approved Count', compute='_compute_stock_picking_counts')

    wika_berita_waiting_count = fields.Integer(string='Wika Berita Waiting Count', compute='_compute_wika_berita_counts')
    wika_berita_uploaded_count = fields.Integer(string='Wika Berita Uploaded Count', compute='_compute_wika_berita_counts')
    wika_berita_approved_count = fields.Integer(string='Wika Berita Approved Count', compute='_compute_wika_berita_counts')

    account_move_waiting_count = fields.Integer(string='Account Move Waiting Count', compute='_compute_account_move_counts')
    account_move_uploaded_count = fields.Integer(string='Account Move Uploaded Count', compute='_compute_account_move_counts')
    account_move_approved_count = fields.Integer(string='Account Move Approved Count', compute='_compute_account_move_counts')

    wika_payment_waiting_count = fields.Integer(string='Wika Payment Waiting Count', compute='_compute_wika_payment_counts')
    wika_payment_uploaded_count = fields.Integer(string='Wika Payment Uploaded Count', compute='_compute_wika_payment_counts')
    wika_payment_approved_count = fields.Integer(string='Wika Payment Approved Count', compute='_compute_wika_payment_counts')

    # Add other fields as needed

    # Compute methods for counts
    @api.depends('name')
    def _compute_purchase_order_counts(self):
        for record in self:
            record.purchase_order_waiting_count = self.env['purchase.order'].search_count([('state', '=', 'po')])
            record.purchase_order_uploaded_count = self.env['purchase.order'].search_count([('state', '=', 'waits')])
            record.purchase_order_approved_count = 0  

    @api.depends('name')
    def _compute_stock_picking_counts(self):
        for record in self:
            record.stock_picking_waiting_count = 0
            record.stock_picking_uploaded_count = 0
            record.stock_picking_approved_count = 0

    # Similar compute methods for other models (wika.berita.acara.pembayaran, account.move, wika.payment.request)

    # Add other methods as needed
