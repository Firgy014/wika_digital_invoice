from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
import pytz
import requests
from num2words import num2words
import math
import json
from urllib.request import Request, urlopen
import logging, json
_logger = logging.getLogger(__name__)

# from terbilang import terbilang
# import requests

class WikaBeritaAcaraPembayaran(models.Model):
    _name = 'wika.berita.acara.pembayaran'
    _description = 'Berita Acara Pembayaran'
    _inherit = ['mail.thread']

    name = fields.Char(string='Nomor BAP', readonly=True, default='/')
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    # po_id = fields.Many2one('purchase.order', string='Nomor PO', required=True,domain=[('state','=','approved')])
    po_id = fields.Many2one('purchase.order', string='Nomor PO',domain=[('state','=','approved')])
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    bap_ids = fields.One2many('wika.berita.acara.pembayaran.line', 'bap_id', string='List BAP', required=True)
    document_ids = fields.One2many('wika.bap.document.line', 'bap_id', string='List Document')
    history_approval_ids = fields.One2many('wika.bap.approval.line', 'bap_id', string='List Approval')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    date = fields.Date('Date')
    state = fields.Selection([
        ('draft', 'Draft'), 
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')], string='Status', readonly=True, default='draft')
    reject_reason = fields.Text(string='Reject Reason')
    step_approve = fields.Integer(string='step approve',default=1)
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)
    end_date = fields.Date(string='Tgl Akhir Kontrak', related="po_id.end_date")
    bap_date = fields.Date(string='Tanggal BAP', required=True)
    bap_type = fields.Selection([
        ('progress', 'Progress'),
        ('uang muka', 'Uang Muka'),
        ('retensi', 'Retensi'),
        ('cut over', 'Cut Over'),
        ], string='Jenis BAP', default='progress')
    price_cut_ids = fields.One2many('wika.bap.pricecut.line', 'po_id')
    signatory_name = fields.Char(string='Nama Penanda Tangan Wika', related="po_id.signatory_name")
    position = fields.Char(string='Jabatan', related="po_id.position")
    address = fields.Char(string='Alamat', related="po_id.address")
    job = fields.Char(string='Pekerjaan', related="po_id.job")
    vendor_signatory_name = fields.Char(string='Nama Penanda Tangan Vendor', related="po_id.vendor_signatory_name")
    vendor_position = fields.Char(string='Jabatan Vendor', related="po_id.vendor_position")
    begin_date = fields.Date(string='Tgl Mulai Kontrak', required=True, related="po_id.begin_date")
    sap_doc_number = fields.Char(string='Nomor Kontrak', required=True, related="po_id.sap_doc_number")
    amount_total = fields.Monetary(string='Total', related="po_id.amount_total")
    currency_id = fields.Many2one('res.currency', string='Currency')
    notes = fields.Html(string='Terms and Conditions', store=True, readonly=False,)
    total_amount = fields.Monetary(string='Total Amount', compute='compute_total_amount')
    total_tax = fields.Monetary(string='Total Tax', compute='compute_total_tax')
    grand_total = fields.Monetary(string='Grand Total', compute='compute_grand_total')
    check_biro = fields.Boolean(compute="_cek_biro")
    tax_totals = fields.Float(
        string="Invoice Totals",
        compute='_compute_tax_totals',
        inverse='_inverse_tax_totals',
        help='Edit Tax amounts if you encounter rounding issues.',
        exportable=False,
    )
    total_qty_gr = fields.Integer(string='Total Quantity', compute='_compute_total_qty_gr')
    total_unit_price_po = fields.Float(string='Total Unit Price PO', compute='_compute_total_unit_price_po')
    total_current_value = fields.Float(string='Nilai saat ini', compute='_compute_total_current_value') #buat sum nilai saat ini
    pph_ids = fields.Many2many('account.tax', string='PPh')
    amount_pph =fields.Float(string="Amount PPh",copy=False)
    total_pph = fields.Monetary(string='Total PPh', compute='compute_total_pph')
    level = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat')
    ], string='Level',compute='_compute_level')
    documents_count = fields.Integer(string='Total Doc', compute='_compute_documents_count')
    invoice_item_count = fields.Integer(string='Total Invoice Item', compute='_compute_invoice_item')

    guarantee_type = fields.Char('Jenis Jaminan')
    guarantee_value = fields.Float('Nilai Jaminan')
    guarantee_numb = fields.Char('No Jaminan')
    guarantee_period = fields.Date('Jangka Waktu Jaminan')
    numb_ba_pho = fields.Char('No Berita Acara PHO')
    pho_date = fields.Date('Tanggal PHO')
    numb_ba_fho = fields.Char('No Berita Acara FHO')
    fho_date = fields.Date('Tanggal FHO')

    # nilai saat ini
    dp_total = fields.Float(string='Total DP', compute='_compute_dp_total', store= True)
    amount_pecentage_tmp = fields.Float(string='amount persen DP', compute='_compute_amount_pecentage_tmp', store= True)
    amount_pecentage_retensi = fields.Float(string='amount persen retensi', compute='_compute_amount_pecentage_retensi', store= True)
    retensi_total = fields.Float(string='Total Retensi', compute='_compute_retensi_total_percentage', store= True)
    dp_qty_total = fields.Float(string='Total QTY DP', compute='_compute_dp_qty', store= True)
    retensi_qty_total = fields.Float(string='Total QTY RETENSI', compute='_compute_retensi_qty', store= True)

    # nilai yang lalu
    last_value = fields.Float(string='nilai yang lalu', compute='_compute_last_value')
    last_quantity = fields.Float(string='Qty yang lalu', compute='_compute_last_value')
    last_dp_total = fields.Float('Potongan uang muka lalu', compute='_compute_last_value')
    last_retensi_total = fields.Float('Potongan retensi lalu', compute='_compute_last_value')
    last_qty_dp = fields.Float('Potongan uang muka QTY lalu')
    last_qty_retensi = fields.Float('Potongan retensi QTY lalu')

    # nilai prestasi s/d saat ini
    qty_sd_saatini = fields.Float('qty s/d saat ini', compute='_compute_qty_sd_saatini',digits='Product Unit of Measure')
    price_sd_saatini = fields.Float('Price s/d saat ini', compute='_compute_price_po_sd_saatini')
    total_sd_saatini = fields.Float('Total s/d saat ini', compute='_compute_total_sd_saatini')

    # nilai potongan uang muka
    qty_dp_saat_ini = fields.Float('Qty uang muka saat ini', compute='_compute_qty_dp_saat_ini', store=True)
    total_dp_saatini = fields.Float('Uang muka saat ini', compute='_compute_total_dp_saatini', store=True)
    dp_sd_saatini = fields.Float('Uang muka s/d saat ini' , compute='_compute_dp_sd_saatini', store=True)

    # nilai potongan retensi
    qty_retensi_saat_ini = fields.Float('Qty retensi saat ini', compute='_compute_qty_retensi_saat_ini', store=True)
    total_retensi_saatini = fields.Float('Retensi saat ini', compute='_compute_total_retensi_saatini', store=True)
    retensi_sd_saatini = fields.Float('Retensi s/d saat ini' , compute='_compute_retensi_sd_saatini', store=True)
    total_pembayaran = fields.Float('Pembayaran', compute='compute_total_pembayaran')
    total_pembayaran_um = fields.Float('Pembayaran uang muka', compute='compute_total_pembayaran_um')
    total_pembayaran_retensi = fields.Float('Pembayaran retensi', compute='compute_total_pembayaran_retensi')
    total_pembayaran_co = fields.Float('Pembayaran cut over', compute='compute_total_pembayaran_cut_over')
    terbilang = fields.Char('Terbilang', compute='_compute_rupiah_terbilang')
    terbilang_um = fields.Char('Terbilang uang muka', compute='_compute_rupiah_terbilang_um')
    terbilang_retensi = fields.Char('Terbilang retensi', compute='_compute_rupiah_terbilang_retensi')
    terbilang_co = fields.Char('Terbilang cut over', compute='_compute_rupiah_terbilang_cut_over')
    is_fully_invoiced = fields.Boolean(string='Fully Invoiced', compute='_compute_fully_invoiced', default=False,store=True)
    is_cut_over = fields.Boolean('is cut over')


    @api.onchange('po_id', 'bap_type')
    def _change_button(self):
        for record in self:
            if record.po_id and record.bap_type == 'cut over' :
                record.is_cut_over=True
                account_move = self.env['account.move.line'].search([('purchase_id','=',record.po_id.id), ('cut_off','=',True),('display_type','=','product')])
                if any(not x.stock_move_id for x in account_move):
                    warning = {
                        'title': 'Warning!',
                        'message': 'Silahkan Mapping Invoice Cut Over terlebih dahulu',
                    }
                    return {'warning': warning}
            else:
                record.is_cut_over = False


    @api.constrains('po_id', 'bap_type')
    def _check_bap_type(self):
        for record in self:
            if record.po_id and record.bap_type != 'cut over':
                account_move = self.env['account.move'].search([('po_id','=',record.po_id.id), ('cut_off','=',True)])
                if account_move:
                    bap = self.env['wika.berita.acara.pembayaran'].search(
                        [('po_id', '=', record.po_id.id), ('bap_type', '=', 'cut over')])
                    if bap:
                        pass
                    else:
                        raise ValidationError(_("Nomor PO tersebut sudah dicatat sebagai cut off di invoice terkait. Silahkan pilih jenis BAP 'Cut Over'."))
            # if record.po_id and record.bap_type == 'cut over':
            #     account_moves = self.env['account.move.line'].search([
            #         ('purchase_id', '=', self.po_id.id),
            #         ('cut_off', '=', True),
            #         ('display_type', '=', 'product')
            #     ])
            #     if any(not x.stock_move_id for x in account_moves):
            #         raise ValidationError(_("Anda belum melakukan mapping GR terhadap Invoice Cut Over!"))


    @api.depends('bap_ids')
    def _compute_fully_invoiced(self):
        tots = 0.0
        for bap_line in self.bap_ids:
            tots += bap_line.qty
        if tots == 0.0:
            self.is_fully_invoiced = True
        else:
            self.is_fully_invoiced = False

    @api.depends('project_id', 'branch_id', 'department_id')
    def _compute_level(self):
        for res in self:
            level=''
            if res.project_id:
                level = 'Proyek'
            elif res.branch_id and not res.department_id and not res.project_id:
                level = 'Divisi Operasi'
            elif res.branch_id and res.department_id and not res.project_id:
                level = 'Divisi Fungsi'
            res.level = level

    # qty s/d saat ini
    @api.depends('bap_ids.qty')
    def _compute_qty_sd_saatini(self):
        for record in self:
            total_qty = sum(record.bap_ids.mapped('qty'))
            record.qty_sd_saatini = record.last_quantity + total_qty

    # unit price s/d saat ini
    @api.depends('bap_ids.unit_price_po')
    def _compute_price_po_sd_saatini(self):
        for record in self:
            total_po = sum(record.bap_ids.mapped('unit_price_po'))
            record.price_sd_saatini = record.last_value + total_po



    # Potongan uang muka computed
    @api.depends('price_cut_ids', 'price_cut_ids.qty', 'price_cut_ids.product_id')
    def _compute_qty_dp_saat_ini(self):
        for record in self:
            total_qty_dp = sum(price_line.qty for price_line in record.price_cut_ids if price_line.product_id.name == 'DP')
            record.qty_dp_saat_ini = total_qty_dp

    @api.depends('price_cut_ids', 'price_cut_ids.amount', 'price_cut_ids.product_id')
    def _compute_total_dp_saatini(self):
        for record in self:
            total_qty_dp = sum(price_line.amount for price_line in record.price_cut_ids if price_line.product_id.name == 'DP')
            record.total_dp_saatini = total_qty_dp

    @api.depends('last_qty_dp', 'qty_dp_saat_ini', 'last_dp_total', 'total_dp_saatini')
    def _compute_dp_sd_saatini(self):
        for record in self:
            record.dp_sd_saatini = (record.last_qty_dp + record.qty_dp_saat_ini) * (record.last_dp_total + record.total_dp_saatini)

    # potongan retensi computed
    @api.depends('price_cut_ids', 'price_cut_ids.qty', 'price_cut_ids.product_id')
    def _compute_qty_retensi_saat_ini(self):
        for record in self:
            total_qty_retensi = sum(price_line.qty for price_line in record.price_cut_ids if price_line.product_id.name == 'RETENSI')
            record.qty_retensi_saat_ini = total_qty_retensi

    @api.depends('price_cut_ids', 'price_cut_ids.amount', 'price_cut_ids.product_id')
    def _compute_total_retensi_saatini(self):
        for record in self:
            total_retensi = sum(price_line.amount for price_line in record.price_cut_ids if price_line.product_id.name == 'RETENSI')
            record.total_retensi_saatini = total_retensi

    @api.depends('last_qty_retensi', 'qty_retensi_saat_ini', 'last_retensi_total', 'total_retensi_saatini')
    def _compute_retensi_sd_saatini(self):
        for record in self:
            record.retensi_sd_saatini = (record.last_qty_retensi + record.qty_retensi_saat_ini) * (record.last_retensi_total + record.total_retensi_saatini)

    @api.depends('qty_sd_saatini', 'price_sd_saatini')
    def _compute_total_sd_saatini(self):
        for record in self:
            record.total_sd_saatini = record.qty_sd_saatini * record.price_sd_saatini


    @api.depends('price_cut_ids', 'price_cut_ids.percentage_amount', 'price_cut_ids.product_id')
    def _compute_amount_pecentage_tmp(self):
        for record in self:
            total_amount_percentage = sum(price_line.percentage_amount for price_line in record.price_cut_ids if price_line.product_id.name == 'DP')
            record.amount_pecentage_tmp = total_amount_percentage

    @api.depends('price_cut_ids', 'price_cut_ids.percentage_amount', 'price_cut_ids.product_id')
    def _compute_amount_pecentage_retensi(self):
        for record in self:
            total_amount_percentage_retensi = sum(price_line.percentage_amount for price_line in record.price_cut_ids if price_line.product_id.name == 'RETENSI')
            record.amount_pecentage_retensi = total_amount_percentage_retensi

    @api.depends('total_amount', 'dp_total', 'retensi_total', 'total_tax', 'total_pph')
    def compute_total_pembayaran(self):
        for record in self:
            total_amount = record.total_amount or 0.0
            dp_total = record.dp_total or 0.0
            retensi_total = record.retensi_total or 0.0
            total_pph = record.total_pph or 0.0

            if record.total_tax:
                total_tax = record.total_tax
            else:
                total_tax = 0.0

            if record.bap_type not in ['uang muka', 'retensi']:
                total_tax_lines = sum(record.bap_ids.tax_ids.filtered(lambda tax: tax.name != 'V3').mapped('amount'))
                total_tax = (total_amount - dp_total - retensi_total) * (total_tax_lines / 100)

            record.total_pembayaran = total_amount - dp_total - retensi_total + total_tax - total_pph

    @api.depends('dp_total', 'total_pph')
    def compute_total_pembayaran_um(self):
        for record in self:
            dp_total = record.dp_total or 0.0
            total_pph = record.total_pph or 0.0
            persentase = 0.11
            total_pembayaran_um = dp_total + (dp_total * persentase) - total_pph
            record.total_pembayaran_um = total_pembayaran_um

    @api.depends('retensi_total', 'total_pph')
    def compute_total_pembayaran_retensi(self):
        for record in self:
            retensi_total = record.retensi_total or 0.0
            total_pph = record.total_pph or 0.0
            persentase = 0.11
            total_pembayaran_retensi = retensi_total + (retensi_total * persentase) - total_pph
            record.total_pembayaran_retensi = total_pembayaran_retensi

    @api.depends('retensi_total', 'total_pph', 'dp_total', 'total_tax', 'total_amount')
    def compute_total_pembayaran_cut_over(self):
        for record in self:
            retensi_total = record.retensi_total or 0.0
            dp_total = record.dp_total or 0.0
            total_tax = record.total_tax or 0.0
            total_pph = record.total_pph or 0.0
            total_amount = record.total_amount or 0.0
            total_pembayaran_co = total_amount - dp_total - retensi_total + total_tax - total_pph
            record.total_pembayaran_co = total_pembayaran_co

    # # funct terbilang
    @api.depends('total_pembayaran')
    def _compute_rupiah_terbilang(self):
        for record in self:
            if record.total_pembayaran:
                # Convert float to integer representation of Rupiah
                rupiah_int = int(record.total_pembayaran)
                # Convert the integer part to words
                rupiah_terbilang = num2words(rupiah_int, lang='id') + " rupiah"
                # If there are cents, add them as well
                sen = int((record.terbilang - rupiah_int) * 100)
                if sen > 0:
                    rupiah_terbilang += " dan " + num2words(sen, lang='id') + " sen"
                record.terbilang = rupiah_terbilang
            else:
                record.terbilang = ""

    @api.depends('total_pembayaran_um')
    def _compute_rupiah_terbilang_um(self):
        for record in self:
            if record.total_pembayaran_um:
                # Convert float to integer representation of Rupiah
                rupiah_int = round(record.total_pembayaran_um)  # Pembulatan angka
                # Convert the integer part to words
                rupiah_terbilang = num2words(rupiah_int, lang='id') + " rupiah"
                # If there are cents, add them as well
                sen = abs(int((record.total_pembayaran_um - rupiah_int) * 100))  # Menghindari masalah pembulatan
                if sen > 0:
                    rupiah_terbilang += " dan " + num2words(sen, lang='id') + " sen"
                record.terbilang_um = rupiah_terbilang
            else:
                record.terbilang_um = ""

    @api.depends('total_pembayaran_retensi')
    def _compute_rupiah_terbilang_retensi(self):
        for record in self:
            if record.total_pembayaran_retensi:
                # Convert float to integer representation of Rupiah
                rupiah_int = round(record.total_pembayaran_retensi)  # Pembulatan angka
                # Convert the integer part to words
                rupiah_terbilang = num2words(rupiah_int, lang='id') + " rupiah"
                # If there are cents, add them as well
                sen = abs(int((record.total_pembayaran_retensi - rupiah_int) * 100))  # Menghindari masalah pembulatan
                if sen > 0:
                    rupiah_terbilang += " dan " + num2words(sen, lang='id') + " sen"
                record.terbilang_retensi = rupiah_terbilang
            else:
                record.terbilang_retensi = ""

    @api.depends('total_pembayaran_co')
    def _compute_rupiah_terbilang_cut_over(self):
        for record in self:
            if record.total_pembayaran_co:
                # Convert float to integer representation of Rupiah
                rupiah_int = round(record.total_pembayaran_co)  # Pembulatan angka
                # Convert the integer part to words
                rupiah_terbilang = num2words(rupiah_int, lang='id') + " rupiah"
                # If there are cents, add them as well
                sen = abs(int((record.total_pembayaran_co - rupiah_int) * 100))  # Menghindari masalah pembulatan
                if sen > 0:
                    rupiah_terbilang += " dan " + num2words(sen, lang='id') + " sen"
                record.terbilang_co = rupiah_terbilang
            else:
                record.terbilang_co = ""

    # @api.depends('bap_date')
    def _compute_last_value(self):
        for record in self:
            if record.bap_date:
                tahun = record.bap_date.year
                tanggal = '%s-01-01' % tahun
                if record.bap_type=='progress':
                    query = """
                        SELECT COALESCE(SUM(sub_total_bap), 0) AS sub_total_bap,
                            COALESCE(SUM(qty_bap), 0) AS qty_bap,
                            COALESCE(AVG(potongan_uang_muka_dp), 0) AS potongan_uang_muka_dp,
                            COALESCE(AVG(potongan_retensi), 0) AS potongan_retensi,
                            COALESCE(AVG(potongan_uang_muka_qty_dp), 0) AS potongan_uang_muka_qty_dp,
                            COALESCE(AVG(potongan_retensi_qty), 0) AS potongan_retensi_qty
                        FROM outstanding_bap
                        WHERE purchase_id = %s AND date_bap >= '%s' AND bap_id < %s AND bap_type in ('%s','cut over')
                    """ % (record.po_id.id, tanggal, record.id, record.bap_type)
                else:
                    query = """
                        SELECT COALESCE(SUM(sub_total_bap), 0) AS sub_total_bap,
                            COALESCE(SUM(qty_bap), 0) AS qty_bap,
                            COALESCE(SUM(potongan_uang_muka_dp), 0) AS potongan_uang_muka_dp,
                            COALESCE(SUM(potongan_retensi), 0) AS potongan_retensi,
                            COALESCE(SUM(potongan_uang_muka_qty_dp), 0) AS potongan_uang_muka_qty_dp,
                            COALESCE(SUM(potongan_retensi_qty), 0) AS potongan_retensi_qty
                        FROM outstanding_bap
                        WHERE purchase_id = %s AND date_bap >= '%s' AND bap_id < %s AND bap_type = '%s' 
                    """ % (record.po_id.id, tanggal, record.id, record.bap_type)
                self.env.cr.execute(query)
                result = self.env.cr.fetchone()
                if result:
                    sub_total_bap = result[0]
                    qty_bap = result[1]
                    potongan_uang_muka_dp = result[2]
                    potongan_retensi = result[3]
                    potongan_uang_muka_qty_dp = result[4]
                    potongan_retensi_qty = result[5]
                else:
                    sub_total_bap = 0.0
                    qty_bap = 0.0
                    potongan_uang_muka_dp = 0.0
                    potongan_retensi = 0.0
                    potongan_uang_muka_qty_dp = 0.0
                    potongan_retensi_qty = 0.0
                record.last_value = sub_total_bap
                record.last_quantity = qty_bap
                record.last_dp_total = potongan_uang_muka_dp
                record.last_retensi_total = potongan_retensi
                record.last_qty_dp = potongan_uang_muka_qty_dp
                record.last_qty_retensi = potongan_retensi_qty
            else:
                record.last_value = 0.0
                record.last_quantity = 0.0
                record.last_dp_total = 0.0
                record.last_retensi_total = 0.0
                record.last_qty_dp = 0.0
                record.last_qty_retensi = 0.0

    # compute Total DP QTY
    @api.depends('price_cut_ids')
    def _compute_dp_qty(self):
        for bap in self:
            retensi_lines = bap.price_cut_ids.filtered(lambda line: line.product_id.name == 'DP')
            bap.dp_qty_total = sum(retensi_lines.mapped('qty'))

    # compute Total Retensi QTY
    @api.depends('price_cut_ids')
    def _compute_retensi_qty(self):
        for bap in self:
            retensi_lines = bap.price_cut_ids.filtered(lambda line: line.product_id.name == 'RETENSI')
            bap.retensi_qty_total = sum(retensi_lines.mapped('qty'))

    # compute DP
    @api.depends('total_amount', 'amount_pecentage_tmp', 'bap_type')
    def _compute_dp_total(self):
        for bap in self:
            if bap.amount_pecentage_tmp > 0:
                bap.dp_total = (bap.total_amount / 100 ) * bap.amount_pecentage_tmp
            elif bap.bap_type == 'uang muka' and bap.total_dp_saatini > 0:
                bap.dp_total = bap.total_dp_saatini
            else :
                bap.dp_total = 0

    # compute retensi
    @api.depends('total_amount', 'amount_pecentage_retensi')
    def _compute_retensi_total_percentage(self):
        for bap in self:
            if bap.amount_pecentage_retensi > 0:
                bap.retensi_total = (bap.total_amount / 100 ) * bap.amount_pecentage_retensi
            elif bap.bap_type == 'retensi' and bap.total_retensi_saatini > 0:
                bap.retensi_total = bap.total_retensi_saatini
            else :
                bap.retensi_total = 0

    # code sequence baru
    @api.model
    def _default_name(self):
        current_date = fields.Date.today()
        year = current_date.year
        sequence = self.env['ir.sequence'].next_by_code('wika.berita.acara.pembayaran') or '001'
        sequence_parts = sequence.split('/')
        sequence_number = sequence_parts[-1]
        return 'BAP/{}/{:03d}'.format(year, int(sequence_number))

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        domain = [('state', '=', 'approved')]
        if self.partner_id:
            domain += [('partner_id', '=', self.partner_id.id)]

            # Mencari pesanan pembelian yang tidak memenuhi kriteria is_qty_available True
            purchase_orders = self.env['purchase.order'].search([
                ('partner_id', '=', self.partner_id.id),
                ('is_qty_available', '=', True)  # Mencari item yang is_qty_available False
            ])

            # Mengumpulkan nomor PO yang harus dikecualikan
            exclude_po_ids = purchase_orders.ids
            if exclude_po_ids:
                domain += [('id', 'not in', exclude_po_ids)]

        return {'domain': {'po_id': domain}}

    #compute total qty gr
    @api.depends('bap_ids.qty')
    def _compute_total_qty_gr(self):
        for record in self:
            total_qty = sum(line.qty for line in record.bap_ids)
            record.total_qty_gr = total_qty

    #compute total unit price PO
    @api.depends('bap_ids.unit_price_po')
    def _compute_total_unit_price_po(self):
        for record in self:
            total_unit_price = sum(line.unit_price_po for line in record.bap_ids)
            record.total_unit_price_po = total_unit_price

    #compute unit price po * qty gr
    @api.depends('bap_ids.qty', 'bap_ids.unit_price_po')
    def _compute_total_current_value(self):
        for record in self:
            total_qty = sum(line.qty for line in record.bap_ids)
            total_unit_price_po = sum(line.unit_price_po for line in record.bap_ids)
            record.total_current_value = total_qty * total_unit_price_po

    @api.model
    def create(self, vals):
        res = super(WikaBeritaAcaraPembayaran, self).create(vals)
        res.name= self.env['ir.sequence'].next_by_code('wika.berita.acara.pembayaran')
        res.assign_todo_first()
        res._compute_cut_over()
        return res


    @api.depends('department_id')
    def _cek_biro(self):
        for x in self:
            if x.department_id:
                biro = self.env['res.branch'].search([('parent_id', '=', x.department_id.id)])
                if biro:
                    x.check_biro = True
                else:
                    x.check_biro = False
            else:
                x.check_biro = False

    def _compute_cut_over(self):
        for record in self:
            if record.po_id and record.bap_type == 'cut over':
                #self.bap_ids = [(2, bap_id.id, 0) for bap_id in self.bap_ids]
                account_moves = self.env['account.move.line'].search([
                    ('purchase_id', '=', record.po_id.id),
                    ('cut_off', '=', True),
                    ('display_type','=','product')
                ])
                for x in record.bap_ids:
                    for data in account_moves:
                        if x.invoice_line_id.id==data.id:
                            if not x.picking_id:
                                x.write({'stock_move_id': data.stock_move_id.id,
                                         'picking_id': data.stock_move_id.picking_id.id})
                            else:
                                x.write({'stock_move_id': data.stock_move_id.id})



    @api.onchange('po_id','bap_type')
    def onchange_po_id(self):

        if self.po_id:
            bap_lines = []
            price_cut_lines = []
            self.bap_ids = [(2, bap_id.id, 0) for bap_id in self.bap_ids]
            if self.bap_type == 'cut over':
                self.is_cut_over = True
                bap_lines = []
                account_moves = self.env['account.move'].search([
                    ('po_id', '=', self.po_id.id),
                    ('cut_off', '=', True)
                ])

                for move in account_moves:
                    for line in move.invoice_line_ids:
                        bap_lines.append((0, 0, {
                            'picking_id': line.picking_id.id,
                            'invoice_line_id': line.id,
                            'stock_move_id': line.stock_move_id.id,
                            'purchase_line_id': line.purchase_line_id.id or False,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom_id.id,
                            'qty': line.quantity,
                            'unit_price': line.price_unit,
                            'tax_ids': [(6, 0, line.tax_ids.ids)],
                            'sub_total': line.price_subtotal,
                            'amount_adjustment': line.price_subtotal,
                            'currency_id': line.currency_id.id,
                        }))

                self.bap_ids = bap_lines
            elif self.bap_type == 'progress':
                stock_pickings = self.env['stock.picking'].search([('po_id', '=', self.po_id.id)])
                # Mengisi price_cut_lines
                self.is_cut_over = False

                for line in self.po_id.price_cut_ids:
                    price_cut_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'percentage_amount': line.persentage_amount,
                        'amount': line.amount,
                    }))

                bap_lines = []
                for picking in stock_pickings.move_ids_without_package.filtered(lambda x: x.sisa_qty_bap>0):
                    bap_lines.append((0, 0, {
                    'picking_id': picking.picking_id.id,
                    'stock_move_id': picking.id,
                    'purchase_line_id':picking.purchase_line_id.id or False,
                    'unit_price_po':picking.purchase_line_id.price_unit,
                    # 'account_move_line_id':aml_src.id or False,
                     'sisa_qty_bap_grses':picking.sisa_qty_bap,
                    'product_uom':picking.product_uom,
                    'product_id': picking.product_id.id,
                    'qty': picking.sisa_qty_bap,
                    'unit_price': picking.purchase_line_id.price_unit,
                    'amount_adjustment': picking.sisa_qty_bap*  picking.purchase_line_id.price_unit,
                    'tax_ids':picking.purchase_line_id.taxes_id.ids,
                    'currency_id':picking.purchase_line_id.currency_id.id
                }))

                self.bap_ids = bap_lines
                self.price_cut_ids = price_cut_lines

    @api.depends('bap_ids.amount_adjustment', 'bap_ids.sub_total','bap_ids.tax_ids', 'bap_type')
    def compute_total_amount(self):
        for record in self:
            if record.bap_type == 'uang muka' :
                total_amount_value = record.po_id.amount_untaxed
                record.total_amount = total_amount_value
            elif record.bap_type == 'retensi' :
                total_amount_value = record.po_id.amount_untaxed
                record.total_amount = total_amount_value
            else:
                total_amount_value = sum(record.bap_ids.mapped('amount_adjustment'))
                record.total_amount = total_amount_value

    @api.depends('total_amount', 'dp_total', 'retensi_total', 'bap_ids.tax_ids', 'bap_type')
    def compute_total_tax(self):
        for record in self:
            if record.bap_type == 'uang muka':
                total_amount_tax = record.po_id.amount_tax
                record.total_tax = math.floor(total_amount_tax)
                # print("TESSSSSSBORRRRRRR", record.total_tax)
            elif record.bap_type == 'retensi':
                total_amount_tax = record.po_id.amount_tax
                record.total_tax = math.floor(total_amount_tax)
                # print("TESSSSSSBORRRRRRRETENSIII", record.total_tax)
            else:
                total_amount = record.total_amount or 0.0
                dp_total = record.dp_total or 0.0
                retensi_total = record.retensi_total or 0.0
                tax_percentage = sum(record.bap_ids.tax_ids.mapped('amount')) / 100.0
                total_tax = (total_amount - dp_total - retensi_total) * tax_percentage
                record.total_tax = math.floor(total_tax)
    


    @api.depends('grand_total', 'total_tax')
    def compute_grand_total(self):
        for record in self:
            record.grand_total = record.total_amount + record.total_tax

    # compute total pph
    # compute total pph revisi
    @api.depends('total_amount', 'bap_type','pph_ids.amount','amount_pph','retensi_total','dp_total')
    def compute_total_pph(self):
        for record in self:
            total_pph = 0.0
            if record.bap_type == 'retensi':
                total_net = record.retensi_total
                for pph in record.pph_ids:
                    total_pph += (total_net * pph.amount) / 100
                record.total_pph = math.floor(total_pph + record.amount_pph)
            else:
                total_net=record.total_amount-record.retensi_total-record.dp_total
                for pph in record.pph_ids:
                    total_pph += (total_net * pph.amount) / 100
                record.total_pph = math.floor(total_pph+record.amount_pph)


    def action_reject(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        cek = False
        level=self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'wika.berita.acara.pembayaran')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level),
                 ('transaction_type', '=', self.po_id.transaction_type)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            groups_id = approval_line_id.groups_id
            if groups_id:
                for x in groups_id.users:
                    if level == 'Proyek' and self.project_id in x.project_ids and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True
                print (cek)
        if cek == True:
            action = {
                'name': ('Reject Reason'),
                'type': "ir.actions.act_window",
                'res_model': "reject.wizard",
                'view_type': "form",
                'target': 'new',
                'view_mode': "form",
                'context': {'groups_id': groups_id.id},
                'view_id': self.env.ref('wika_berita_acara_pembayaran.bap_reject_wizard_form').id,
            }
            return action
        else:
            raise ValidationError('User Akses Anda tidak berhak Reject!')


    def assign_todo_first(self):
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'wika.berita.acara.pembayaran')], limit=1)
        for res in self:
            level=res.level
            first_user = False
            if level:
                approval_id = self.env['wika.approval.setting'].sudo().search(
                    [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',res.po_id.transaction_type)], limit=1)
                approval_line_id = self.env['wika.approval.setting.line'].search([
                    ('sequence', '=', 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                groups_id = approval_line_id.groups_id
                if groups_id:
                    for x in groups_id.users:
                        if level == 'Proyek' and res.project_id in x.project_ids:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == res.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == res.department_id:
                            first_user = x.id
                print(first_user)
                #     # Createtodoactivity
                if first_user:
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': 4,
                        'res_model_id': model_id.id,
                        'res_id': res.id,
                        'user_id': first_user,
                        'nomor_po': res.po_id.name,
                        'date_deadline': fields.Date.today() + timedelta(days=2),
                        'state': 'planned',
                        'summary': f"Need Upload Document {model_id.name}!"
                    })

            # Get Document Setting
            document_list = []
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

            if doc_setting_id:
                for document_line in doc_setting_id:
                    document_list.append((0, 0, {
                        'bap_id': res.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                res.document_ids = document_list
            else:
                raise AccessError(
                    "Either approval and/or document settings are not found. Please configure it first in the settings menu.")


    def push_bap(self):
        url_token = self.env['wika.integration'].sudo().search([('name', '=', 'URL_GET_TOKEN')], limit=1)
        url_push = self.env['wika.integration'].sudo().search([('name', '=', 'URL_SEND_BAP')], limit=1)
        auth = ('WIKA_INT', 'Initial123')
        headers = {'x-csrf-token': 'fetch'}
        input_list = []
        data = {}

        # arrange the payload
        for bap in self.bap_ids:
            if bap.picking_id.pick_type == 'gr':
                doc_no = bap.picking_id.name
            elif bap.picking_id.pick_type == 'ses':
                doc_no = bap.picking_id.origin

            matdoc_year = str(
                fields.Date.to_date(bap.picking_id.scheduled_date).year) if bap.picking_id.scheduled_date else ''
            data = {
                "COMPANY_CODE": "A000",
                "DOCUMENT_NO": doc_no,
                "MATDOC_YEAR": matdoc_year,
                "STATUS": "X"
            }
            input_list.append(data)

        # GET req
        response = requests.get(url_token.url, headers=headers, auth=auth)
        fetched_token = response.headers.get('x-csrf-token')
        fetched_cookies = response.cookies.get_dict()

        payload = json.dumps({
            "INPUT": input_list
        })

        # POST req
        post_headers = {
            'x-csrf-token': fetched_token,
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw=='
        }
        response_post = requests.request("POST", url_push.url, headers=post_headers, data=payload,
                                         cookies=fetched_cookies)



    def action_submit(self):
        if not self.bap_ids:
            raise ValidationError('List BAP tidak boleh kosong. Mohon isi List BAP terlebih dahulu!')

        for record in self:
            if any(not line.document for line in record.document_ids):
                raise ValidationError('Document belum di unggah, mohon unggah file terlebih dahulu!')
            if record.bap_type =='cut over' and any(not line.stock_move_id for line in record.bap_ids):
                raise ValidationError('Data Invoice cut over belum di mapping!')

            if any(line.state == 'rejected' for line in record.document_ids):
                raise ValidationError('Document belum di ubah setelah reject, silahkan cek terlebih dahulu!')

            if any(line.state =='rejected' for line in record.document_ids):
                raise ValidationError('Document belum di ubah setelah reject, silahkan cek terlebih dahulu!')

        cek = False
        level=self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'wika.berita.acara.pembayaran')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level),
                 ('transaction_type', '=', self.po_id.transaction_type)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', 1),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            print(approval_line_id)
            groups_id = approval_line_id.groups_id
            if groups_id:
                for x in groups_id.users:
                    if level == 'Proyek' and self.project_id in x.project_ids and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True

        if cek == True:
            if self.activity_ids:
                for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                    if x.user_id.id == self._uid:
                        x.status = 'approved'
                        x.action_done()
                self.state = 'uploaded'
                self.step_approve += 1
                self.env['wika.bap.approval.line'].sudo().create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Submit Document',
                    'bap_id': self.id
                })
                groups_line = self.env['wika.approval.setting.line'].search([
                    ('level', '=', level),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                groups_id_next = groups_line.groups_id
                if groups_id_next:
                    for x in groups_id_next.users:
                        if level == 'Proyek' and  self.project_id in x.project_ids:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                            first_user = x.id
                    if first_user:
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': self.env['ir.model'].sudo().search(
                                [('model', '=', 'wika.berita.acara.pembayaran')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'nomor_po': self.po_id.name,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': """Need Approval Document BAP"""
                        })
                    self.push_bap()
        else:
            raise ValidationError('User Akses Anda tidak berhak Submit!')

    def action_approve(self):
        for record in self:
            if record.bap_type!='cut_over':
                if any(x.picking_id.state!='approved' for x in record.bap_ids):
                    raise ValidationError('Document GR/SES belum Lengkap silahkan lengkapi terlebih dahulu')

        documents_model = self.env['documents.document'].sudo()
        cek = False
        model_id = self.env['ir.model'].search([('model','=', 'wika.berita.acara.pembayaran')], limit=1)
        level=self.level
        if level:
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level),
                 ('transaction_type', '=', self.po_id.transaction_type)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')

            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            print(approval_line_id)
            groups_id = approval_line_id.groups_id
            if groups_id:
                print(groups_id.name)
                for x in groups_id.users:
                    if level == 'Proyek' and  self.project_id in x.project_ids and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True

        if cek == True:
            if approval_id.total_approve == self.step_approve:
                self.state = 'approved'
                self.env['wika.bap.approval.line'].create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Approved',
                    'bap_id': self.id
                })
                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'BAP')], limit=1)
                if folder_id:
                    facet_id = self.env['documents.facet'].sudo().search([
                        ('name', '=', 'Documents'),
                        ('folder_id', '=', folder_id.id)
                    ], limit=1)
                    for doc in self.document_ids.filtered(lambda x: x.state in ('uploaded','rejected')):
                        doc.state = 'verified'
                        attachment_id = self.env['ir.attachment'].sudo().create({
                            'name': doc.filename,
                            'datas': doc.document,
                            'res_model': 'documents.document',
                        })
                        if attachment_id:
                            tag = self.env['documents.tag'].sudo().search([
                                ('facet_id', '=', facet_id.id),
                                ('name', '=', doc.document_id.name)
                            ], limit=1)
                            documents_model.create({
                                'attachment_id': attachment_id.id,
                                'folder_id': folder_id.id,
                                'tag_ids': tag.ids,
                                'partner_id': doc.bap_id.partner_id.id,
                                'purchase_id': self.po_id.id,
                                'bap_id': self.id,
                            })
                if self.activity_ids:
                    for x in self.activity_ids.filtered(lambda x: x.status  != 'approved'):
                        if x.user_id.id == self._uid:
                            x.status = 'approved'
                            x.action_done()
            else:
                first_user = False
                # Createtodoactivity
                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level', '=', level),
                    ('sequence', '=', self.step_approve + 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                print("groups", groups_line_next)
                groups_id_next = groups_line_next.groups_id
                if groups_id_next:
                    print(groups_id_next.name)
                    for x in groups_id_next.users:
                        if level == 'Proyek' and  self.project_id in x.project_ids:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                            first_user = x.id

                    if first_user:
                        self.step_approve += 1
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': self.env['ir.model'].sudo().search(
                                [('model', '=', 'wika.berita.acara.pembayaran')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'nomor_po': self.po_id.name,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': """Need Approval Document BAP"""
                        })
                        self.env['wika.bap.approval.line'].create({
                            'user_id': self._uid,
                            'groups_id': groups_id.id,
                            'date': datetime.now(),
                            'note': 'Verified',
                            'bap_id': self.id
                        })
                        if self.activity_ids:
                            for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                                if x.user_id.id == self._uid:
                                    print(x.status)
                                    x.status = 'approved'
                                    x.action_done()
                    else:
                        raise ValidationError('User Role Next Approval Belum di Setting!')

        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def _compute_documents_count(self):
        for record in self:
            record.documents_count = self.env['documents.document'].search_count(
                [('purchase_id', '=', record.po_id.id)])
    @api.depends('po_id')
    def _compute_invoice_item(self):
        for record in self:
            record.invoice_item_count = self.env['account.move.line'].search_count(
                [('purchase_id', '=', record.po_id.id),('cut_off','=',True)])

    def get_invoice_item(self):
        view_tree_id = self.env.ref("wika_account_move.view_wika_account_move_line_tree", raise_if_not_found=False)

        return {
            'name': _('Invoice Cut Over'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_ids': [(view_tree_id, 'tree')],
            'res_id': self.id,
            'domain': [('purchase_id', '=', self.po_id.id),('cut_off','=',True),('display_type','=','product')],
            'context': {'default_purchase_id': self.po_id.id},
        }

    def get_documents(self):
        self.ensure_one()
        view_kanban_id = self.env.ref("documents.document_view_kanban", raise_if_not_found=False)
        view_kanban_id = self.env.ref("documents.document_view_kanban", raise_if_not_found=False)

        view_tree_id = self.env.ref("documents.documents_view_list", raise_if_not_found=False)

        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree',
            'res_model': 'documents.document',
            'view_ids': [(view_kanban_id, 'kanban'),(view_tree_id, 'tree')],
            'res_id': self.id,
            'domain': [('purchase_id', '=', self.po_id.id),('folder_id','in',('PO','GR/SES','BAP'))],
            'context': {'default_purchase_id': self.po_id.id},
        }

    def action_cancel(self):
        self.write({'state': 'draft'})

    @api.onchange('po_id')
    def onchange_po(self):
        self.partner_id = self.po_id.partner_id.id
        self.branch_id = self.po_id.branch_id.id
        self.department_id = self.po_id.department_id.id if self.po_id.department_id else False
        self.project_id = self.po_id.project_id.id if self.po_id.project_id else False

    def unlink(self):
        for record in self:
            if record.state=='draft':
                record.activity_ids.unlink()
                record.bap_ids.unlink()
                record.price_cut_ids.unlink()
            else:
                raise ValidationError('Tidak dapat menghapus ketika status Berita Acara Pembayaran (BAP) dalam keadaan Upload atau Approve')
        return super(WikaBeritaAcaraPembayaran, self).unlink()

    def action_print_bap(self):
        if self.bap_type == 'progress':
            return self.env.ref('wika_berita_acara_pembayaran.report_wika_berita_acara_pembayaran_action').report_action(self)
        elif self.bap_type == 'uang muka':
            return self.env.ref('wika_berita_acara_pembayaran.report_wika_berita_acara_pembayaran_um_action').report_action(self)
        elif self.bap_type == 'retensi':
            return self.env.ref('wika_berita_acara_pembayaran.report_wika_berita_acara_pembayaran_retensi_action').report_action(self)
        elif self.bap_type == 'cut over':
            self._compute_cut_over()
            if self.bap_type =='cut over' and any(not line.stock_move_id for line in self.bap_ids):
                raise ValidationError('Data Invoice cut over belum di mapping!')
            return self.env.ref('wika_berita_acara_pembayaran.report_wika_berita_acara_pembayaran_cut_over_action').report_action(self)
        else:
            return super(WikaBeritaAcaraPembayaran, self).action_print_bap()

    # @api.onchange('end_date')
    # def _check_contract_expiry_on_save(self):
    #     if self.end_date and self.end_date < fields.Date.today():
    #         raise UserError(_("Tanggal akhir kontrak PO sudah kadaluarsa. Silakan perbarui kontrak segera!"))
    #

    #


class WikaBeritaAcaraPembayaranLine(models.Model):
    _name = 'wika.berita.acara.pembayaran.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    picking_id = fields.Many2one('stock.picking', string='NO GR/SES')
    stock_move_id = fields.Many2one('stock.move', string='Stock Move')
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Item')
    purchase_line_id= fields.Many2one('purchase.order.line', string='Purchase Line')
    unit_price_po = fields.Monetary(string='Price Unit PO')
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Float(string='Quantity' ,digits='Product Unit of Measure')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    tax_ids = fields.Many2many('account.tax', string='Tax')
    currency_id = fields.Many2one('res.currency', string='Currency')
    unit_price = fields.Monetary(string='Unit Price')
    adjustment = fields.Boolean(string='Adjustment',default=False)
    amount_adjustment = fields.Monetary(string='Amount Adjustment')
    sub_total = fields.Monetary(string='Subtotal', compute='compute_sub_total')
    tax_amount = fields.Monetary(string='Tax Amount', compute='compute_tax_amount')
    current_value = fields.Monetary(string='Current Value', compute='_compute_current_value')
    sisa_qty_bap_grses = fields.Float(string='Sisa BAP',digits='Product Unit of Measure')
    qty_invoiced = fields.Float(string='Total Invoiced', compute='_compute_invoiced_bap_qty')

    @api.depends('bap_id')
    def _compute_invoiced_bap_qty(self):
        for record in self:
            move_line_ids = self.env['account.move.line'].sudo().search([('bap_line_id', '=', record.id)])
            total_invoiced_bap_qty = sum(move_line.quantity for move_line in move_line_ids)
            record.qty_invoiced = total_invoiced_bap_qty


    # @api.constrains('qty')
    # def _check_qty_limit(self):
    #     for line in self:
    #         if line.qty > line.sisa_qty_bap_grses:
    #             raise ValidationError('Quantity tidak boleh melebihi sisa quantity pada GR/SES!')

    @api.constrains('qty')
    def _check_qty_limit(self):
        for line in self:
            if line.bap_id.bap_type != 'cut over' and line.qty > line.sisa_qty_bap_grses:
                raise ValidationError('Quantity tidak boleh melebihi sisa quantity pada GR/SES!')

    @api.depends('tax_ids', 'sub_total')
    def compute_sub_total(self):
        for record in self:
            tax_rate = sum(record.tax_ids.mapped('amount')) / 100  # Assuming tax amount is in percentage
            record.sub_total = record.sub_total + (record.sub_total * tax_rate)

    @api.depends('tax_ids', 'sub_total')
    def compute_tax_amount(self):
        for record in self:
            tax_amount_value = sum(record.tax_ids.mapped('amount')) * record.sub_total / 100
            record.tax_amount = tax_amount_value

    @api.depends('qty', 'unit_price')
    def compute_sub_total(self):
        for record in self:
            record.sub_total = record.qty * record.unit_price

    @api.onchange('qty','adjustment')
    def change_qty(self):
        for record in self:
            if record.adjustment != True:
                record.amount_adjustment = record.qty * record.unit_price

    @api.constrains('picking_id')
    def _check_picking_id(self):
        for record in self:
            if not record.picking_id and record.bap_id.bap_type != 'cut over':
                raise ValidationError('Field "NO GR/SES" harus diisi. Tidak boleh kosong!')

    @api.depends('unit_price_po', 'qty','adjustment')
    def _compute_current_value(self):
        for record in self:
            if record.adjustment != True:
                record.current_value = record.qty * record.unit_price_po
            else:
                record.current_value = record.amount_adjustment

class WikaBapDocumentLine(models.Model):
    _name = 'wika.bap.document.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(string="Upload File", attachment=True, store=True, required=True)
    filename = fields.Char(string="File Name")
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], string='Status', default='waiting')
    # text_upload_here = fields.Char('')

    @api.onchange('document')
    def onchange_document(self):
        if self.document:
            self.state = 'uploaded'
    
    @api.constrains('document', 'filename')
    def _check_attachment_format(self):
        for record in self:
            if record.filename and not record.filename.lower().endswith('.pdf'):
                raise ValidationError('Tidak dapat mengunggah file selain berformat PDF!')

    def buttonClickEvent(self):
        return

class WikaBapApprovalLine(models.Model):
    _name = 'wika.bap.approval.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    groups_id = fields.Many2one('res.groups', string='Groups', readonly=True)
    date = fields.Datetime('Date', readonly=True)
    note = fields.Char('Note', readonly=True)

class WikaPriceCutLine(models.Model):
    _name = 'wika.bap.pricecut.line'
    _description = 'Wika Price Cut Line'

    po_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    product_id = fields.Many2one('product.product', string='Product')
    amount = fields.Float(string='Amount')
    qty = fields.Integer(string='Quantity')
    percentage_amount = fields.Float(string='Amount (%)')

    # @api.constrains('percentage_amount')
    # def _check_percentage_amount(self):
    #     for record in self:
    #         if record.percentage_amount > 5:
    #             raise ValidationError("Persentasi tidak boleh melebihi dari 5%")

