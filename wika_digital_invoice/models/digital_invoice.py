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
    # status = fields.Selection([
    #     ('waiting', 'Waiting'),
    #     ('uploaded', 'Uploaded'),
    #     ('approved', 'Approved')
    # ], string='Status')
    model = fields.Selection([
        ('init', ' '),
        ('po', 'Purchase Orders'),
        ('grses', 'GR/SES'),
        ('bap', 'Berita Acara Pembayaran'),
        ('inv', 'Invoice'),
        ('pr', 'Pengajuan Pembayaran')
    ], string='Menu', default='init')
    # purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    # picking_id = fields.Many2one('stock.picking', string='GR/SES')
    # bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='Berita Acara Pembayaran')
    # invoice_id = fields.Many2one('account.move', string='Invoice')
    # payment_id = fields.Many2one('wika.payment.request', string='Pengajuan Pembayaran')

    # purchase_ids = fields.Many2many('purchase.order', string='Purchase Orders')
    # picking_ids = fields.Many2many('stock.picking', string='Stock Pickings')
    # bap_ids = fields.One2many('wika.berita.acara.pembayaran', string='Berita Acara Pembayaran')
    # invoice_ids = fields.One2many('account.move', string='Account Moves')
    # payment_ids = fields.One2many('wika.payment.request', string='Pengajuan Pembayaran')

    # Essentials
    color = fields.Integer(string='Color')

    # Codes
    purchase_code = fields.Selection([
        ('waiting', 'Waiting PO Documents'),
        ('uploaded', 'PO Documents Uploaded'),
        ('approved', 'PO Documents Approved')],
    string='Type of PO', compute='_compute_code')

    picking_code = fields.Selection([
        ('waiting', 'Waiting GR/SES Documents'),
        ('uploaded', 'GR/SES Documents Uploaded'),
        ('approved', 'GR/SES Documents Approved')],
    string='Type of GR/SES', compute='_compute_code')

    bap_code = fields.Selection([
        ('waiting', 'Waiting BAP Documents'),
        ('uploaded', 'BAP Documents Uploaded'),
        ('approved', 'BAP Documents Approved')],
    string='Type of BAP', compute='_compute_code')

    invoice_code = fields.Selection([
        ('waiting', 'Waiting Invoice Documents'),
        ('uploaded', 'Invoice Documents Uploaded'),
        ('approved', 'Invoice Documents Approved')],
    string='Type of Invoice', compute='_compute_code')

    payment_code = fields.Selection([
        ('waiting', 'Waiting PR Documents'),
        ('uploaded', 'PR Documents Uploaded'),
        ('approved', 'PR Documents Approved')],
    string='Type of PR', compute='_compute_code')

    # Counting records
    # Purchase
    # count_purchase_po = fields.Integer(compute='_compute_purchase_count')
    # count_purchase_uploaded = fields.Integer(compute='_compute_purchase_count')
    # count_purchase_approved = fields.Integer(compute='_compute_purchase_count')
    count_purchase = fields.Integer(string='Total PO')
    count_purchase_po = fields.Integer(string='Total Doc Waiting PO')
    count_purchase_uploaded = fields.Integer(string='Total Doc Uploaded PO')
    count_purchase_approved = fields.Integer(string='Total Doc Approved PO')
    
    # Picking
    # count_picking = fields.Integer(compute='_compute_picking_count')
    # count_picking_waits = fields.Integer(compute='_compute_picking_waits_count')
    # count_picking_uploaded = fields.Integer(compute='_compute_picking_uploaded_count')
    # count_picking_approved = fields.Integer(compute='_compute_picking_approved_count')
    count_picking = fields.Integer(string='Total GR/SES')
    count_picking_waits = fields.Integer(string='Total Doc Waiting GR/SES')
    count_picking_uploaded = fields.Integer(string='Total Doc Uploaded GR/SES')
    count_picking_approved = fields.Integer(string='Total Doc Approved GR/SES')

    # BAP
    # count_bap_waiting = fields.Integer(compute='_compute_bap_count')
    # count_bap_uploaded = fields.Integer(compute='_compute_bap_count')
    # count_bap_approved = fields.Integer(compute='_compute_bap_count')
    count_bap = fields.Integer(string='Total BAP')
    count_bap_waiting = fields.Integer(string='Total Doc Waiting BAP')
    count_bap_uploaded = fields.Integer(string='Total Doc Uploaded BAP')
    count_bap_approved = fields.Integer(string='Total Doc Approved BAP')

    # Invoice
    # count_invoice_waiting = fields.Integer(compute='_compute_invoice_count')
    # count_invoice_uploaded = fields.Integer(compute='_compute_invoice_count')
    count_invoice = fields.Integer(string='Total Invoice')
    count_invoice_waiting = fields.Integer(string='Total Doc Waiting Invoice')
    count_invoice_uploaded = fields.Integer(string='Total Doc Uploaded Invoice')
    count_invoice_approved = fields.Integer(string='Total Doc Approved Invoice')

    # Payment Request
    # count_payment_waiting = fields.Integer(compute='_compute_payment_count')
    # count_payment_uploaded = fields.Integer(compute='_compute_payment_count')
    count_payment = fields.Integer(string='Total PR')
    count_payment_waiting = fields.Integer(string='Total Doc Waiting PR')
    count_payment_uploaded = fields.Integer(string='Total Doc Uploaded PR')
    count_payment_approved = fields.Integer(string='Total Doc Approved PR')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            res = super(DigitalInvoiceOverview, self).create(vals)

            if 'po' in vals.values():
                res.count_purchase = self.env['purchase.order'].search_count([('id', '!=', False)])
                res.count_purchase_po = self.env['purchase.order'].search_count([('state', '!=', 'po')])
                res.count_purchase_uploaded = self.env['purchase.order'].search_count([('state', '!=', 'uploaded')])
                res.count_purchase_approved = self.env['purchase.order'].search_count([('state', '!=', 'approved')])
            
            elif 'grses' in vals.values():
                res.count_picking = self.env['stock.picking'].search_count([('id', '!=', False)])
                res.count_picking_waits = self.env['stock.picking'].search_count([('state', '!=', 'waits')])
                res.count_picking_uploaded = self.env['stock.picking'].search_count([('state', '!=', 'uploaded')])
                res.count_picking_approved = self.env['stock.picking'].search_count([('state', '!=', 'approved')])
                print(res.count_picking_approved)
            
            elif 'bap' in vals.values():
                res.count_bap = self.env['wika.berita.acara.pembayaran'].search_count([('id', '!=', False)])
                res.count_bap_waiting = self.env['wika.berita.acara.pembayaran'].search_count([('state', '!=', 'draft')])
                res.count_bap_uploaded = self.env['wika.berita.acara.pembayaran'].search_count([('state', '!=', 'upload')])
                res.count_bap_approved = self.env['wika.berita.acara.pembayaran'].search_count([('state', '!=', 'approve')])

            elif 'inv' in vals.values():
                res.count_invoice = self.env['account.move'].search_count([('id', '!=', False)])
                res.count_invoice_waiting = self.env['account.move'].search_count([('state', '!=', 'draft')])
                res.count_invoice_uploaded = self.env['account.move'].search_count([('state', '!=', 'upload')])
                res.count_invoice_approved = self.env['account.move'].search_count([('state', '!=', 'approve')])

            elif 'pr' in vals.values():
                res.count_payment = self.env['wika.payment.request'].search_count([('id', '!=', False)])
                res.count_payment_waiting = self.env['wika.payment.request'].search_count([('state', '!=', 'draft')])
                res.count_payment_uploaded = self.env['wika.payment.request'].search_count([('state', '!=', 'upload')])
                res.count_payment_approved = self.env['wika.payment.request'].search_count([('state', '!=', 'approve')])

        return res
    
    def _compute_code(self):
        for record in self:
            if record.model == 'po':
                record.purchase_code = 'waiting'
            elif record.model == 'grses':
                record.picking_code = 'waiting'
            elif record.model == 'bap':
                record.bap_code = 'waiting'
            elif record.model == 'inv':
                record.invoice_code = 'waiting'
            elif record.model == 'pr':
                record.payment_code = 'waiting'


    # def _compute_picking_count(self):
    #     domains = {
    #         'count_picking_waits': [('state', '=', 'waits')],
    #         'count_picking_uploaded': [('state', '=', 'uploaded')],
    #         'count_picking_approved': [('state', '=', 'approved')],
    #         'count_picking': [('state', 'in', ('waits', 'uploaded', 'approved'))],
    #         # 'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('waits'))],
    #         # 'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting'))],
    #     }
    #     for field in domains:
    #         data = self.env['stock.picking']._read_group(domains[field] +
    #             [('state', 'not in', ('approved', 'waits')), ('picking_type_id', 'in', self.ids)],
    #             ['picking_type_id'], ['picking_type_id'])
    #         count = {
    #             x['picking_type_id'][0]: x['picking_type_id_count']
    #             for x in data if x['picking_type_id']
    #         }
    #         for record in self:
    #             record[field] = count.get(record.id, 0)

    # def _compute_picking_count(self):
    #     total_picking = self.env['stock.picking'].search_count([('id', '!=', False)])
    #     for record in self:
    #         if total_picking != 0:
    #             rec

    # def _compute_picking_waits_count(self):
    #     total_waits = self.env['stock.picking'].search_count([('state', '=', 'waits')])
    #     print("TOTWAITS", total_waits)
    #     for record in self:
    #         if record.model == 'grses':
    #             if 'Wait' in record.name:
    #                 if total_waits != 0:
    #                     record.count_picking_waits = total_waits
    #                     record.picking_code = 'waiting'
    #                 else:
    #                     record.count_picking_waits = 25
    #                     record.picking_code = 'waiting'
    #             else:
    #                 record.count_picking_waits = 25
    #                 record.picking_code = 'waiting'
    #         else:
    #             record.count_picking_waits = 0
    #             record.picking_code = 'waiting'

    # def _compute_picking_uploaded_count(self):
    #     total_uploaded = self.env['stock.picking'].search_count([('state', '=', 'uploaded')])
    #     print("TOTUPLOAD", total_uploaded)
    #     for record in self:
    #         if record.model == 'grses':
    #             if 'Upload' in record.name:
    #                 if total_uploaded != 0:
    #                     record.count_picking_uploaded = total_uploaded
    #                     record.picking_code = 'uploaded'
    #                 else:
    #                     record.count_picking_uploaded = 25
    #                     record.picking_code = 'uploaded'
    #             else:
    #                 record.count_picking_uploaded = 25
    #                 record.picking_code = 'uploaded'
    #         else:
    #             record.count_picking_uploaded = 0
    #             record.picking_code = 'uploaded'                
    
    # def _compute_picking_approved_count(self):
    #     total_approved = self.env['stock.picking'].search_count([('state', '=', 'approved')])
    #     print("TOTAPPR", total_approved)
    #     for record in self:
    #         if record.model == 'grses':
    #             if 'Approve' in record.name:
    #                 if total_approved != 0:
    #                     record.count_picking_approved = total_approved
    #                     record.picking_code = 'approved'
    #                 else:
    #                     record.count_picking_approved = 0
    #                     record.picking_code = 'approved'
    #             else:
    #                 record.count_picking_approved = 0
    #                 record.picking_code = 'approved'
    #         else:
    #             record.count_picking_approved = 0
    #             record.picking_code = 'approved'

    # def _compute_picking_code(self):
    #     for record in self:
    #         if record.count_picking    

    def get_action_picking_tree_ready(self):
        # print("GET ACTION PICKING TREE READY")
        return None
    
    # def _compute_name(self):
    #     for record in self:
    #         if record.status:
    #             if record.status == 'waiting':
    #                 record.name = 'Waiting'
    #             elif record.status == 'uploaded':
    #                 record.name = 'Uploaded'
    #             elif record.status == 'approved':
    #                 record.name = 'Approved'

# class InheritPurchaseDigitalInvoice(models.Model):
#     _inherit = 'purchase.order'

#     digital_invoice_id = fields.Many2one('wika.digital.invoice', string='Digital Invoice')

# class InheritPickingDigitalInvoice(models.Model):
#     _inherit = 'stock.picking'

#     digital_invoice_id = fields.Many2one('wika.digital.invoice', string='Digital Invoice')

# class InheritBAPDigitalInvoice(models.Model):
#     _inherit = 'wika.berita.acara.pembayaran'

#     digital_invoice_id = fields.Many2one('wika.digital.invoice', string='Digital Invoice')

# class InheritAccountMoveDigitalInvoice(models.Model):
#     _inherit = 'account.move'

#     digital_invoice_id = fields.Many2one('wika.digital.invoice', string='Digital Invoice')

# class InheritPaymentRequestDigitalInvoice(models.Model):
#     _inherit = 'wika.payment.request'

#     digital_invoice_id = fields.Many2one('wika.digital.invoice', string='Digital Invoice')
