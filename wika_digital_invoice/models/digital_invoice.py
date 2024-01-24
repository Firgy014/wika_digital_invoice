import time
from odoo import api, models, fields

DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_SERVER_TIME_FORMAT = "%H:%M:%S"
DEFAULT_SERVER_DATETIME_FORMAT = "%s %s" % (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_TIME_FORMAT
)

class DigitalInvoiceOverview(models.Model):
    _name = 'wika.digital.invoice'
    _description = 'Digital Invoice'

    # Master records
    name = fields.Char(string='Name')
    status = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved')
    ], string='Status')
    model = fields.Selection([
        ('init', ' '),
        ('po', 'Purchase Orders'),
        ('grses', 'GR/SES'),
        ('bap', 'Berita Acara Pembayaran'),
        ('inv', 'Invoice'),
        ('pr', 'Pengajuan Pembayaran')
    ], string='Menu', default='init')
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    picking_id = fields.Many2one('stock.picking', string='GR/SES')
    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='Berita Acara Pembayaran')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    payment_id = fields.Many2one('wika.payment.request', string='Pengajuan Pembayaran')

    # Essentials
    color = fields.Integer(string='Color')

    # Codes
    picking_code = fields.Selection([
        ('waiting', 'Waiting GR/SES Documents'),
        ('uploaded', 'GR/SES Documents Uploaded'),
        ('approved', 'GR/SES Documents Approved')],
    string='Type of Operation')

    # Counting records
    # Purchase
    # count_purchase_po = fields.Integer(compute='_compute_purchase_count')
    # count_purchase_uploaded = fields.Integer(compute='_compute_purchase_count')
    # count_purchase_approved = fields.Integer(compute='_compute_purchase_count')

    # Picking
    count_picking = fields.Integer(compute='_compute_picking_count')
    count_picking_waits = fields.Integer(compute='_compute_picking_count')
    count_picking_uploaded = fields.Integer(compute='_compute_picking_count')
    count_picking_approved = fields.Integer(compute='_compute_picking_count')

    # BAP
    # count_bap_waiting = fields.Integer(compute='_compute_bap_count')
    # count_bap_uploaded = fields.Integer(compute='_compute_bap_count')
    # count_bap_approved = fields.Integer(compute='_compute_bap_count')

    # Invoice
    # count_invoice_waiting = fields.Integer(compute='_compute_invoice_count')
    # count_invoice_uploaded = fields.Integer(compute='_compute_invoice_count')
    # count_invoice_approved = fields.Integer(compute='_compute_invoice_count')

    # Paymemt Request
    # count_payment_waiting = fields.Integer(compute='_compute_payment_count')
    # count_payment_uploaded = fields.Integer(compute='_compute_payment_count')
    # count_payment_approved = fields.Integer(compute='_compute_payment_count')

    def _compute_picking_count(self):
        domains = {
            'count_picking_waits': [('state', '=', 'waits')],
            'count_picking_uploaded': [('state', '=', 'uploaded')],
            'count_picking_approved': [('state', '=', 'approved')],
            'count_picking': [('state', 'in', ('waits', 'uploaded', 'approved'))],
            # 'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('waits'))],
            # 'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting'))],
        }
        for field in domains:
            data = self.env['stock.picking']._read_group(domains[field] +
                [('state', 'not in', ('approved', 'waits')), ('picking_type_id', 'in', self.ids)],
                ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)

    def get_action_picking_tree_ready(self):
        print("GET ACTION PICKING TREE READY")
        return None
    
