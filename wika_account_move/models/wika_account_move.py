from odoo import fields, models, api, _
import requests
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
from datetime import datetime,timedelta
import math, re
from odoo.tools.float_utils import float_compare
from dateutil.relativedelta import relativedelta
from odoo.tools import (
    date_utils,
    float_compare
)
import base64
from pypdf import PdfReader, PdfWriter
from io import BytesIO
from PIL import Image
import logging, json
_logger = logging.getLogger(__name__)
from num2words import num2words

def convertToMbSize(binary_file_size):
    match_file = re.match(r'^(\d+(?:\.\d+)?)\s*([KMG]?)B?$', binary_file_size.decode("utf-8"), re.IGNORECASE)
    if not match_file:
        match_file = re.match(r'^(?\d+(?:\.\d+)?\s*([bytes]?)B?$', binary_file_size.decode("utf-8"), re.IGNORECASE)

    file_size = float(match_file.group(1))
    file_extention = match_file.group(2)

    if file_extention == "K":
        file_size /= 1024
    elif file_extention == "M":
        file_size *= 1024
    elif file_extention == "G":
        file_size *= 1024
    else:
        file_size /= 1024**2

    return file_size

class WikaInheritedAccountMove(models.Model):
    _inherit = 'account.move'

    name = fields.Char(
        string='Number',
        default='Draft', inverse='_inverse_name', readonly=False,
        copy=False,
        tracking=True,
        index='trigram',
    )
    bap_id = fields.Many2one(
        'wika.berita.acara.pembayaran',
        string='BAP',
        domain="""[
            ('state', '=', 'approved'),
            ('is_cut_over', '!=', True),
            ('is_fully_invoiced', '!=', True)
        ]"""
    )
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    document_ids = fields.One2many('wika.invoice.document.line', 'invoice_id', string='Document Line', required=True)
    history_approval_ids = fields.One2many('wika.invoice.approval.line', 'invoice_id', string='History Approval Line')
    reject_reason_account = fields.Text(string='Reject Reason')
    step_approve = fields.Integer(string='Step Approve',default=1)
    no_doc_sap = fields.Char(string='No Doc SAP')
    no_invoice_vendor = fields.Char(string='Nomor Invoice Vendor',required=True, default='-')
    invoice_number = fields.Char(string='Invoice Number')
    baseline_date = fields.Date(string='Baseline Date')
    retention_due = fields.Date(string='Retention Due')
    po_id = fields.Many2one('purchase.order', store=True, readonly=False,
        string='Nomor PO',domain=[('state','=','approved')])
    amount_invoice = fields.Float(string='Amount Invoice')
    tax_totals = fields.Binary(
        string="Invoice Totals",
        compute='_compute_tax_totals',
        inverse='_inverse_tax_totals',
        help='Edit Tax amounts if you encounter rounding issues.',
        exportable=False,
    )
    special_gl_id = fields.Many2one('wika.special.gl', string='Special GL')
    check_biro = fields.Boolean(compute="_cek_biro")

    pph_ids = fields.Many2many('account.tax', string='PPH')
    total_pph = fields.Monetary(string='Total PPH', readonly=False, compute='_compute_total_pph', tracking=True)
    pph_amount = fields.Monetary(string='PPH Amount', readonly=False)

    price_cut_ids = fields.One2many('wika.account.move.pricecut.line', 'move_id', string='Other Price Cut')
    account_id = fields.Many2one(comodel_name='account.account')
    date = fields.Date(string='Posting Date', default=lambda self: fields.Date.today())
    status_invoice = fields.Char(string='Status Invoice',compute='_compute_status_invoice')
    status_invoice_rel = fields.Char(string='Status Invoice',related='status_invoice',store=True)
    approval_stage = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat'),
    ], string='Position')
    payment_block = fields.Selection([
        ('B', 'Default Invoice'),
        ('C', 'Pengajuan Ke Divisi'),
        ('D', 'Pengajuan Ke Pusat'),
        ('" "', 'Free For Payment (Sudah Approve)'),
        ('K', 'Dokumen Kembali'),
    ], string='Payment Block', default='B')
    payment_method = fields.Selection([
        ('transfer tunai', 'Transfer Tunai (TT)'),
        ('fasilitas', 'Fasilitas'),
    ], string='Payment Method')
    status_payment = fields.Selection([
        ('Not Request', 'Not Request'),
        ('Request Proyek', 'Request Proyek'),
        ('Request Divisi', 'Request Divisi'),
        ('Request Pusat', 'Request Pusat'),
        ('Ready To Pay', 'Ready To Pay'),
        ('Paid', 'Paid')
    ], string='Payment State',default='Not Request')  
    payment_request_date= fields.Date(string='Payment Request Date')
    nomor_payment_request= fields.Char(string='Nomor Payment Request')
    is_approval_checked = fields.Boolean(string="Approval Checked", compute='_compute_is_approval_checked', default=False)
    is_wizard_cancel = fields.Boolean(string="Is cancel", default=True)
    is_upd_api_pph_amount = fields.Boolean(string="Is Update PPH From API?", default=False)
    total_pembayaran = fields.Float('Pembayaran', compute='compute_total_pembayaran')
    total_pembayaran_um = fields.Float('Pembayaran uang muka', compute='compute_total_pembayaran_um')
    total_pembayaran_retensi = fields.Float('Pembayaran retensi', compute='compute_total_pembayaran_retensi')
    terbilang = fields.Char('Terbilang', compute='_compute_rupiah_terbilang')

    # compute bap progress
    @api.depends('bap_id.total_amount', 'bap_id.dp_total', 'bap_id.retensi_total', 'bap_id.total_tax', 'pph_amount')
    def compute_total_pembayaran(self):
        for record in self:
            total_amount = record.bap_id.total_amount or 0.0
            dp_total = record.bap_id.dp_total or 0.0
            retensi_total = record.bap_id.retensi_total or 0.0
            pph_amount = record.pph_amount or 0.0

            if record.bap_id.total_tax:
                total_tax = record.bap_id.total_tax
            else:
                total_tax = 0.0

            total_tax_lines = 0.0
            for line in record.bap_id.bap_ids:
                total_tax_lines += sum(line.tax_ids.filtered(lambda tax: tax.name not in ('V3', 'VA', 'VB')).mapped('amount'))

            total_tax = (total_amount - dp_total - retensi_total) * (total_tax_lines / 100)
            record.total_pembayaran = total_amount - dp_total - retensi_total + total_tax - pph_amount

    # compute bap uang muka
    @api.depends('bap_id.dp_total', 'pph_amount')
    def compute_total_pembayaran_um(self):
        for record in self:
            dp_total = record.bap_id.dp_total or 0.0
            pph_amount = record.pph_amount or 0.0
            total_pembayaran_um = dp_total - pph_amount
            record.total_pembayaran_um = total_pembayaran_um

    # compute bap retensi
    @api.depends('bap_id.retensi_total', 'pph_amount')
    def compute_total_pembayaran_retensi(self):
        for record in self:
            retensi_total = record.bap_id.retensi_total or 0.0
            pph_amount = record.pph_amount or 0.0
            total_pembayaran_retensi = retensi_total - pph_amount
            record.total_pembayaran_retensi = total_pembayaran_retensi

    # list currency
    def _get_currency_info(self, currency_name):
        currency_info = {
            'EUR': {'lang': 'en', 'currency_name': 'Euro', 'cent_name': 'cents'},
            'IDR': {'lang': 'id', 'currency_name': 'rupiah', 'cent_name': 'sen'},
            'USD': {'lang': 'en', 'currency_name': 'US Dollar', 'cent_name': 'cents'},
            'GBP': {'lang': 'en', 'currency_name': 'British Pound', 'cent_name': 'pence'},
            'AUD': {'lang': 'en', 'currency_name': 'Australian Dollar', 'cent_name': 'cents'},
            'JPY': {'lang': 'en', 'currency_name': 'Yen', 'cent_name': 'yen'},
        }

        return currency_info.get(currency_name, {'lang': 'id', 'currency_name': 'rupiah', 'cent_name': 'sen'})

    # terbilang digabungkan
    @api.depends('total_pembayaran', 'total_pembayaran_um', 'total_pembayaran_retensi', 'currency_id', 'bap_id.bap_type')
    def _compute_rupiah_terbilang(self):
        for record in self:
            amount = 0.0
            if record.bap_id.bap_type == 'uang muka':
                amount = record.total_pembayaran_um
            elif record.bap_id.bap_type == 'progress':
                amount = record.total_pembayaran
            elif record.bap_id.bap_type == 'retensi':
                amount = record.total_pembayaran_retensi

            if amount:
                currency = self._get_currency_info(record.currency_id.name)
                lang = currency['lang']
                currency_name = currency['currency_name']
                cent_name = currency['cent_name']

                total_int = int(amount)
                terbilang = num2words(total_int, lang=lang) + " " + currency_name
                cents = int((amount - total_int) * 100)
                if cents > 0:
                    if lang == 'en':
                        terbilang += " and " + num2words(cents, lang=lang) + " " + cent_name
                    else:
                        terbilang += " dan " + num2words(cents, lang=lang) + " " + cent_name
                record.terbilang = terbilang
            else:
                record.terbilang = ""

    @api.onchange('is_mp_approved')
    def _onchange_is_mp_approved(self):
        if not self.is_mp_approved:
            # Hapus document_ids yang terkait dengan BAP
            self.document_ids.filtered(lambda doc: doc.document_id.name == 'BAP').unlink()

        if self.is_mp_approved:
            model_model = self.env['ir.model'].sudo()
            document_setting_model = self.env['wika.document.setting'].sudo()
            model_id = model_model.search([('model', '=', 'account.move')], limit=1)
            bap_document_setting = document_setting_model.search([('name', '=', 'BAP'), ('model_id', '=', model_id.id)], limit=1)

            if bap_document_setting:
                document_list = [(0, 0, {
                    'invoice_id': self.id,
                    'document_id': bap_document_setting.id,
                    'state': 'waiting'
                })]
                self.document_ids = document_list
            else:
                raise AccessError("Setting dokumen BAP tidak ditemukan!")

    def action_print_bap_invoice(self):
        if self.bap_type == 'progress':
            return self.env.ref('wika_account_move.report_bap_progress_action').report_action(self)
        elif self.bap_type == 'uang muka':
            return self.env.ref('wika_account_move.report_bap_uang_muka_action').report_action(self)
        elif self.bap_type == 'retensi':
            return self.env.ref('wika_account_move.report_bap_retensi_action').report_action(self)
        else:
            return super(WikaInheritedAccountMove, self).action_print_bap()

    # validasi posting date jika -1 bulan
    @api.constrains('posting_date')
    def _check_posting_date(self):
        for record in self:
            today = fields.Date.today()
            first_day_of_current_month = today.replace(day=1)
            first_day_of_previous_month = (first_day_of_current_month - timedelta(days=1)).replace(day=1)

            if record.posting_date < first_day_of_previous_month:
                raise ValidationError("Tanggal posting tidak boleh lebih awal dari bulan sebelumnya.")

    _sql_constraints = [
        ('name_invoice_uniq', 'unique (name, year)', 'The name of the invoice must be unique per year !')
    ]

    def _must_check_constrains_date_sequence(self):
        # OVERRIDES sequence.mixin
        return False

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        # bypass _onchange_journal_id
        return

    _sql_constraints = [
        ('name_invoice_uniq', 'unique (name, year)', 'The name of the invoice must be unique per year !')
    ]

    def _must_check_constrains_date_sequence(self):
        # OVERRIDES sequence.mixin
        return False

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        # bypass _onchange_journal_id
        return

    @api.depends('history_approval_ids.is_show_wizard', 'history_approval_ids.user_id')
    def _compute_is_approval_checked(self):
        current_user = self.env.user
        for move in self:
            move.is_approval_checked = any(line.is_show_wizard for line in move.history_approval_ids if line.user_id == current_user)

    @api.depends('total_line', 'pph_ids.amount','pph_amount','retensi_total','dp_total')
    def _compute_total_pph(self):
        for record in self:
            total_pph = 0.0
            total_net = record.total_line - record.retensi_total - record.dp_total
            if record.pph_amount > 0:
                record.total_pph = math.floor(record.pph_amount)
            else:
                for pph in record.pph_ids:
                    total_pph += (total_net* pph.amount) / 100
                record.total_pph = math.floor(total_pph)
                

    @api.depends('history_approval_ids')
    def _compute_status_invoice(self):
        for record in self:
            max_id = max(record.history_approval_ids.mapped('id'), default=False)
            current_user = record.user_id
            if max_id:
                max_record = record.history_approval_ids.filtered(lambda x: x.id == max_id)
                record.status_invoice = f"{max_record.note} by {max_record.groups_id.name}"
            else:
                record.status_invoice = f"Created by {current_user.name}"

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

    @api.onchange('invoice_date')
    def _onchange_invoice_date(self):
        if isinstance(self, bool):
            return self
        if len(self) != 1:
            raise ValidationError("Hanya satu record yang diharapkan diperbarui!")

        if self.invoice_date != False and self.bap_id:
            if self.invoice_date < self.bap_id.bap_date:
                raise ValidationError("Document Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")
            else:
                pass
        else:
            pass

    @api.onchange('date')
    def _onchange_posting_date(self):
        if not self.date or not self.bap_id or not self.bap_id.bap_date:
            return
        if isinstance(self, bool):
            return self
        if len(self) != 1:
            raise ValidationError("Hanya satu record yang diharapkan diperbarui!")
        if self.bap_id:
            if self.date < self.bap_id.bap_date:
                raise ValidationError("Posting Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('uploaded', 'Uploaded'),
            ('approved', 'Approved'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )
    amount_total_footer = fields.Float(string='Net Amount', compute='_compute_amount_total', store=True)
    level = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat')
    ], string='Level', compute='_compute_level', default='Proyek')
    valuation_class = fields.Selection([
        ('material', 'Material'),
        ('alat', 'Alat'),
        ('upah', 'Upah'),
        ('subkont', 'Subkont'),
        ('btl', 'BTL')
    ], compute='_compute_get_lowest_valuation_class', string='Valuation Class')

    documents_count = fields.Integer(string='Total Doc', compute='_compute_documents_count')
    no_faktur_pajak = fields.Char(string='Tax Number', default='0000000000000000')
    dp_total = fields.Float(string='Total DP', compute='_compute_potongan_total', store= True)
    retensi_total = fields.Float(string='Total Retensi', compute='_compute_potongan_total', store= True)
    total_tax = fields.Monetary(string='Total Tax', compute='compute_total_tax')

    amount_total_payment = fields.Float(string='Amount Invoice', compute='_compute_amount_total_payment', store=True)
    total_line = fields.Float(string='Total Line', compute='_compute_total_line')
    is_approval_checked = fields.Boolean(string="Approval Checked", compute='_compute_is_approval_checked')
    is_mp_approved = fields.Boolean(string='Approved by MP', default=False, store=True)
    cut_off = fields.Boolean(string='Cut Off',default=False,copy=False)
    ap_type = fields.Selection([
        ('ap_po', 'AP PO'),
        ('ap_nonpo', 'AP NON PO')
    ], string='Invoice AP Type', compute='_compute_ap_type', store=True)
    amount_scf = fields.Float(string='Amount SCF')
    total_scf_cut = fields.Float(string='Total Potongan SCF', compute='_compute_total_scf_cut')
    journal_item_sap_ids = fields.One2many('wika.account.move.journal.sap', 'invoice_id', string='Journal SAP')
    total_ap_sap = fields.Float(string='Total AP SAP', compute='_compute_total_ap_sap')
    is_waba = fields.Boolean(string='Invoice Waba', compute='_compute_is_waba')
    bap_type = fields.Char(string='Jenis BAP', compute='_compute_bap_type', store=True)
    activity_user_id = fields.Many2one('res.users', string='ToDo User', store=True)
    error_narration = fields.Char(string='Error Narration')
    is_paralel_rejection = fields.Boolean(string="Invoice Included in Reject Paralel", default=False)

    #penambahan dari wika integration
    is_generated = fields.Boolean(string='Generated to TXT File', default=False)
    year = fields.Char(string='Invoice Year')
    dp_doc = fields.Char(string='DP Doc')
    retensi_doc = fields.Char(string='Retensi Doc')
    sap_amount_payment = fields.Float('Amount Payment', tracking=True)
    amount_due = fields.Float('Amount Due', compute='_compute_amount_due')
    amount_idr = fields.Float(string='Amount IDR', store=True)
    is_pr_sent_to_sap = fields.Boolean(string='Is Have a PR Sent to SAP', default=False, store=True)
    is_verified_as_pr = fields.Char(string='Is Have a PR Sent to SAP', store=True, default='no')
    lpad_payment_reference = fields.Char(string='LPAD Payment Reference', compute='_compute_lpad_payment_reference', store=True)

    @api.depends('payment_reference')
    def _compute_lpad_payment_reference(self):
        for rec in self:
            if rec.payment_reference:
                rec.lpad_payment_reference = rec.payment_reference.zfill(10)
            else:
                rec.lpad_payment_reference = ''

    @api.depends('amount_total_footer', 'sap_amount_payment', 'total_line')
    def _compute_amount_due(self):
        _logger.info("# === _compute_amount_due === #")
        for rec in self:
            amount_due = rec.amount_total_footer - rec.sap_amount_payment
            _logger.info("Total Footer %s Total SAP Amount Payment %s Residual Amount %s" % (str(rec.amount_total_footer), str(rec.sap_amount_payment), str(amount_due)))
            rec.amount_due = amount_due
            rec._compute_status_payment()
    
    @api.depends('amount_due')
    def _compute_status_payment(self):
        for rec in self:
            _logger.info("# === _compute_status_payment === #")
            if rec.state != 'draft':
                if rec.amount_due <= 0:
                    rec.status_payment = 'Paid'
                else:
                    rec.status_payment = 'Not Request'
            else:
                rec.status_payment = 'Not Request'

    @api.depends('bap_id.bap_type')
    def _compute_bap_type(self):
        for record in self:
            if record.bap_id:
                record.bap_type = record.bap_id.bap_type

    @api.depends('no_faktur_pajak', 'total_tax')
    def _compute_is_waba(self):
        for record in self:
            if record.no_faktur_pajak:
                if record.no_faktur_pajak.startswith(('010', '040', '050')):
                    record.is_waba = True
                elif record.no_faktur_pajak.startswith('030'):
                    record.is_waba = False
                else:
                    record.is_waba = False
            else:
                record.is_waba = False

    @api.depends('journal_item_sap_ids.amount')
    def _compute_total_ap_sap(self):
        for record in self:
            record.total_ap_sap = sum(line.amount for line in record.journal_item_sap_ids)

    @api.depends('price_cut_ids.amount', 'amount_scf')
    def _compute_total_scf_cut(self):
        for record in self:
            total_price_cut = sum(line.amount for line in record.price_cut_ids if line.product_id.name == 'Potongan SCF')
            record.total_scf_cut = total_price_cut + record.amount_scf

    @api.depends('po_id')
    def _compute_ap_type(self):
        for record in self:
            record.ap_type = 'ap_po' if record.po_id else 'ap_nonpo'
    journal_item_sap_ids = fields.One2many('wika.account.move.journal.sap', 'invoice_id', string='Journal SAP')
    total_ap_sap = fields.Float(string='Total AP SAP', compute='_compute_total_ap_sap')

    @api.depends('journal_item_sap_ids.amount')
    def _compute_total_ap_sap(self):
        for record in self:
            record.total_ap_sap = sum(line.amount for line in record.journal_item_sap_ids)

    def _compute_name_wdigi(self):
        for rec in self:
            sequence = self.env['ir.sequence'].sudo().next_by_code('invoice_number_sequence') or '/'
            seq = sequence.split("/")
            if rec.invoice_date:
                bulan = rec.invoice_date.strftime('%m')
                tahun = rec.invoice_date.strftime('%Y')
                rec.name = "%s/%s/%s/%s" % (seq[0], str(tahun), str(bulan), seq[3])

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError('Tidak dapat menghapus ketika status Invoice dalam keadaan Upload atau Approve')
        for record in self:
                record.activity_ids.unlink()
                record.document_ids.unlink()
                record.history_approval_ids.unlink()
                record.price_cut_ids.unlink()
        return super(WikaInheritedAccountMove, self).unlink()

    # @api.depends('date')
    # def _compute_name_wika(self):
    #     for record in self:
    #         if record.date:
    #             year = str(record.date.year)
    #             month = str(record.date.month).zfill(2)
    #             next_number = 1
    #             while True:
    #                 name = f"INV/{year}/{month}/{str(next_number).zfill(5)}"
    #                 existing_record = self.env['account.move'].search([('name', '=', name)], limit=1)
    #                 if not existing_record:
    #                     record.name = name
    #                     break
    #                 next_number += 1
    #                 if next_number > 99999:
    #                     raise ValidationError("Naming sequence limit exceeded.")

    @api.depends('total_line', 'invoice_line_ids', 'dp_total','retensi_total', 'invoice_line_ids.tax_ids')
    def compute_total_tax(self):
        for record in self:
            total_line = record.total_line or 0.0
            dp_total = record.dp_total or 0.0
            retensi_total = record.retensi_total or 0.0
            tax_percentage = sum(record.invoice_line_ids.tax_ids.mapped('amount')) / 100.0
            total_tax = (total_line - dp_total - retensi_total) * tax_percentage
            record.total_tax = math.floor(total_tax)

    @api.depends('total_line', 'price_cut_ids.percentage_amount','price_cut_ids.product_id')
    def _compute_potongan_total(self):
        for x in self:
            persentage_dp = sum(line.percentage_amount for line in x.price_cut_ids if line.product_id.name == 'DP')
            persentage_retensi = sum(line.percentage_amount for line in x.price_cut_ids if line.product_id.name == 'RETENSI')
            x.dp_total = 0.0
            x.retensi_total = 0.0
            if persentage_dp > 0:
                x.dp_total = math.floor((x.total_line / 100 ) * persentage_dp)
            if persentage_retensi > 0:
                x.retensi_total = math.floor((x.total_line / 100 ) * persentage_retensi)

    @api.depends('total_line', 'dp_total', 'retensi_total', 'total_tax', 'total_scf_cut')
    def _compute_amount_total_payment(self):
        for record in self:
            amount_total_payment = record.total_line - record.dp_total - record.retensi_total - record.total_scf_cut + record.total_tax
            if record.currency_id.name == 'IDR':
                record.amount_total_payment = round(amount_total_payment)
            else:
                record.amount_total_payment = amount_total_payment


    def _compute_documents_count(self):
        for record in self:
            if record.po_id:
                domain = [
                    ('folder_id', 'in', ['PO', 'GR/SES', 'BAP', 'Invoicing']),
                    '|', ('bap_id', '=', record.bap_id.id), ('purchase_id', '=', record.po_id.id),
                ]
                po_number = record.po_id.name if record.po_id else None

                if po_number:
                    domain.append(('purchase_id.name', '=', po_number))
            else:
                domain = [
                    ('folder_id', 'in', ['Invoicing']),
                    ('invoice_id', '=', record.id),
                ]

            record.documents_count = self.env['documents.document'].search_count(domain)


    # Compute document count with unique names 
    # def _compute_documents_count(self):
    #     for record in self:
    #         if record.po_id:
    #             domain = [
    #                 ('folder_id', 'in', ['PO', 'GR/SES', 'BAP', 'Invoicing']),
    #                 ('tag_ids', '!=', False),
    #                 ('purchase_id', '=', record.po_id.id),
    #             ]
    #             po_number = record.po_id.name if record.po_id else None

    #             if po_number:
    #                 domain.append(('purchase_id.name', '=', po_number))
                
    #             # Fetch all documents matching the domain
    #             documents = self.env['documents.document'].search(domain)
                
    #             # Extract unique document names
    #             unique_names = list(set(documents.mapped('name')))
                
    #             # Update the domain to filter by unique names
    #             domain.append(('name', 'in', unique_names))
                
    #             # Fetch documents with unique names
    #             filtered_documents = self.env['documents.document'].search(domain)
                
    #             # Group documents by owner_id and count the records for each owner
    #             owner_counts = {}
    #             for doc in filtered_documents:
    #                 owner_id = doc.owner_id.id
    #                 if owner_id in owner_counts:
    #                     owner_counts[owner_id] += 1
    #                 else:
    #                     owner_counts[owner_id] = 1

    #             # Identify the owner_id with the highest number of records
    #             if owner_counts:
    #                 max_owner_id = max(owner_counts, key=owner_counts.get)

    #                 # Update the domain to filter by the identified owner_id
    #                 domain.append(('owner_id', '=', max_owner_id))

    #             # Count documents with the updated domain
    #             record.documents_count = self.env['documents.document'].search_count(domain)
    #         else:
    #             domain = [
    #                 ('folder_id', 'in', ['Invoicing']),
    #                 ('invoice_id', '=', record.id),
    #                 ('tag_ids', '!=', False)
    #             ]
                
    #             # Fetch all documents matching the domain
    #             documents = self.env['documents.document'].search(domain)
                
    #             # Extract unique document names
    #             unique_names = list(set(documents.mapped('name')))
                
    #             # Update the domain to filter by unique names
    #             domain.append(('name', 'in', unique_names))
                
    #             # Fetch documents with unique names
    #             filtered_documents = self.env['documents.document'].search(domain)
                
    #             # Group documents by owner_id and count the records for each owner
    #             owner_counts = {}
    #             for doc in filtered_documents:
    #                 owner_id = doc.owner_id.id
    #                 if owner_id in owner_counts:
    #                     owner_counts[owner_id] += 1
    #                 else:
    #                     owner_counts[owner_id] = 1

    #             # Identify the owner_id with the highest number of records
    #             if owner_counts:
    #                 max_owner_id = max(owner_counts, key=owner_counts.get)

    #                 # Update the domain to filter by the identified owner_id
    #                 domain.append(('owner_id', '=', max_owner_id))

    #             # Count documents with the updated domain
    #             record.documents_count = self.env['documents.document'].search_count(domain)


    @api.depends('invoice_line_ids')
    def _compute_get_lowest_valuation_class(self):
        valuation_classes = [line.product_id.valuation_class for line in self.invoice_line_ids if
                             line.product_id and line.product_id.valuation_class]
        if valuation_classes:
            self.valuation_class = min(valuation_classes)
        else:
            self.valuation_class = False

    def get_documents(self):
        self.ensure_one()
        view_kanban_id = self.env.ref("documents.document_view_kanban", raise_if_not_found=False)
        view_tree_id = self.env.ref("documents.documents_view_list", raise_if_not_found=False)

        domain = [
            ('folder_id', 'in', ['PO', 'GR/SES', 'BAP', 'Invoicing']),
            '|', ('bap_id', '=', self.bap_id.id), ('purchase_id', '=', self.po_id.id)
        ]

        po_number = self.po_id.name if self.po_id else None

        if po_number:
            domain.append(('purchase_id.name', '=', po_number))

        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree',
            'res_model': 'documents.document',
            'view_ids': [(view_kanban_id.id, 'kanban'), (view_tree_id.id, 'tree')],
            'res_id': self.id,
            'domain': domain,
            'context': {'default_purchase_id': self.po_id.id},
        }


    # # get documents action with unique names 
    # def get_documents(self):
    #     self.ensure_one()
    #     view_kanban_id = self.env.ref("documents.document_view_kanban", raise_if_not_found=False)
    #     view_tree_id = self.env.ref("documents.documents_view_list", raise_if_not_found=False)

    #     # Initial domain construction
    #     domain = [
    #         ('folder_id', 'in', ['PO', 'GR/SES', 'BAP', 'Invoicing']),
    #         ('purchase_id', '=', self.po_id.id),
    #         ('tag_ids', '!=', False),
    #     ]
        
    #     po_number = self.po_id.name if self.po_id else None

    #     if po_number:
    #         domain.append(('purchase_id.name', '=', po_number))
        
    #     # Fetch all documents matching the domain
    #     documents = self.env['documents.document'].search(domain)
        
    #     # Extract unique document names
    #     unique_names = list(set(documents.mapped('name')))
        
    #     # Update the domain to filter by unique names
    #     domain.append(('name', 'in', unique_names))
        
    #     # Fetch documents with unique names
    #     filtered_documents = self.env['documents.document'].search(domain)
        
    #     # Group documents by owner_id and count the records for each owner
    #     owner_counts = {}
    #     for doc in filtered_documents:
    #         owner_id = doc.owner_id.id
    #         if owner_id in owner_counts:
    #             owner_counts[owner_id] += 1
    #         else:
    #             owner_counts[owner_id] = 1

    #     # Identify the owner_id with the highest number of records
    #     if owner_counts:
    #         max_owner_id = max(owner_counts, key=owner_counts.get)

    #         # Update the domain to filter by the identified owner_id
    #         domain.append(('owner_id', '=', max_owner_id))

    #     return {
    #         'name': _('Documents'),
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'kanban,tree',
    #         'res_model': 'documents.document',
    #         'view_ids': [(view_kanban_id.id, 'kanban'), (view_tree_id.id, 'tree')],
    #         'res_id': self.id,
    #         'domain': domain,
    #         'context': {'default_purchase_id': self.po_id.id},
    #     }



    @api.depends('project_id', 'branch_id', 'department_id')
    def _compute_level(self):
        for res in self:
            level=False
            if res.project_id:
                level = 'Proyek'
            elif res.branch_id and not res.department_id and not res.project_id:
                level = 'Divisi Operasi'
            elif res.branch_id and res.department_id and not res.project_id:
                level = 'Divisi Fungsi'
            res.level = level

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            return {'domain': {'bap_id': [('partner_id', '=', self.partner_id.id), ('state', '=', 'approved'), ('is_cut_over', '!=', True)]}}
        else:
            return {'domain': {'bap_id': [('state', '=', 'approved'), ('is_cut_over', '!=', True)]}}

    @api.onchange('name', 'highest_name')
    def _onchange_name_warning(self):
        # Disable _onchange_name_warning
        return
    
    @api.depends('invoice_line_ids.price_unit', 'invoice_line_ids.quantity', 'invoice_line_ids.adjustment', 'invoice_line_ids.amount_adjustment')
    def _compute_total_line(self):
        for record in self:
            total = 0
            for line in record.invoice_line_ids:
                if line.adjustment:
                    total += line.amount_adjustment
                else:
                    total += line.price_unit * line.quantity
            
            if record.currency_id.name == 'IDR':
                record.total_line = round(total)
            else:
                record.total_line = total

    @api.depends('total_line', 'total_pph', 'dp_total', 'retensi_total', 'total_scf_cut', 'is_waba')
    def _compute_amount_total(self):
        for move in self:
            amount_total = move.total_line - move.dp_total - move.retensi_total - move.total_pph - move.total_scf_cut
            if move.is_waba:
                amount_total += move.total_tax

            if move.currency_id.name == 'IDR':
                move.amount_total_footer = round(amount_total)
            else:
                move.amount_total_footer = amount_total

    @api.depends('partner_id.bill_coa_type', 'valuation_class','retensi_total')
    def compute_account_payable(self):
        for record in self:
            record.account_id = False
            if record.level == 'Proyek':
                level=record.level.lower()
            else:
                level='nonproyek'
            account_setting_model = self.env['wika.setting.account.payable'].sudo().search([
                    ('valuation_class', '=', record.valuation_class),
                    ('assignment', '=', level),
                    ('bill_coa_type', '=', record.partner_id.bill_coa_type)
                ], limit=1)
            if account_setting_model:
                record.account_id = account_setting_model.account_id.id
            if record.retensi_total>0:
                record.retention_due=record.invoice_date_due+ relativedelta(months=+6)


    @api.onchange('partner_id', 'valuation_class')
    def onchange_account_payable(self):
        for record in self:
            record.account_id = False
            account_setting_model = self.env['wika.setting.account.payable'].sudo()

            if record.level == 'Proyek' and record.valuation_class:
                account_setting_id = account_setting_model.search([
                    ('valuation_class', '=', record.valuation_class),
                    ('assignment', '=', record.level.lower()),
                    ('bill_coa_type', '=', record.partner_id.bill_coa_type)
                ], limit=1)
                record.account_id = account_setting_id.account_id.id
                return {'domain': {'pph_ids': [('id', 'in', account_setting_id.pph_ids.ids)]}}
            elif record.level != 'Proyek' and record.valuation_class:
                account_setting_id = account_setting_model.search([
                    ('valuation_class', '=', record.valuation_class),
                    ('assignment', '=', 'nonproyek'),
                    ('bill_coa_type', '=',  record.partner_id.bill_coa_type)
                ], limit=1)
                record.account_id = account_setting_id.account_id.id
                return {'domain': {'pph_ids': [('id', 'in', account_setting_id.pph_ids.ids)]}}

    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        _logger.info("# === _compute_name === #")
        return
    
    @api.depends('journal_id', 'date')
    def _compute_highest_name(self):
        _logger.info("# === _compute_highest_name === #")
        return
    
    def _get_accounting_date(self, invoice_date, has_tax):
        return invoice_date

    @api.model_create_multi
    def create(self, vals_list):
        record = super(WikaInheritedAccountMove, self).create(vals_list)
        if record.ap_type == 'ap_po':
            record.assign_todo_first()
        elif record.ap_type == 'ap_nonpo':
            record.assign_todo_first_without_activities()

        if record.name == 'Draft':
            record._compute_name_wdigi()

        # if isinstance(record, bool):
        #     return record
        # if len(record) != 1:
        #     raise ValidationError("Hanya satu record yang diharapkan diperbarui!")
        
        if record.bap_id:
            #document date
            if record.invoice_date != False and record.invoice_date < record.bap_id.bap_date and record.cut_off != True:
                raise ValidationError("Document Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")
            
            #posting date
            if record.ap_type == 'ap_po':
                if record.date != False and record.date < record.bap_id.bap_date and record.cut_off!=True:
                    raise ValidationError("Posting Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")

            # Posting date validation
            if record.date and record.date < record.bap_id.bap_date and not record.cut_off:
                raise ValidationError("Posting Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")
            
        return record

    def write(self, values):
        for rec in self:
            # _logger.info("# === ACCOUNT MOVE WRITE === #")
            # _logger.info(str(values))
            record = super(WikaInheritedAccountMove, rec).write(values)

            if isinstance(record, bool):
                return record
            if len(record) != 1:
                raise ValidationError("Hanya satu record yang diharapkan diperbarui!")

            # document date
            if record.invoice_date != False and record.invoice_date < record.bap_id.bap_date and record.cut_off!=True:
                raise ValidationError("Document Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")
            else:
                pass

            # # posting date
            if record.date != False and record.date < record.bap_id.bap_date and record.cut_off!=True:
                raise ValidationError("Posting Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")
            else:
                pass
        
        return record

    # Refresh all records to ensure is_waba and amount total is successfully computed
    def _cron_refresh_record_values(self):
        invoices = self.env['account.move'].search([])
        if invoices:
            for invoice in invoices:
                if invoice.is_waba:
                    invoice.refresh()
                    _logger.info('Successfully refreshing all values for Invoice: %s', invoice.name)

    def _replace_document_object(self, folder_name, document_ids, po_id):
        documents_model = self.env['documents.document'].sudo()
        folder_id = self.env['documents.folder'].sudo().search([('name', '=', folder_name)], limit=1)
        if folder_id:
            facet_id = self.env['documents.facet'].sudo().search([
                ('name', '=', 'Documents'),
                ('folder_id', '=', folder_id.id)
            ], limit=1)
            for doc in document_ids:
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
                        'partner_id': po_id.partner_id.id,
                        'purchase_id': po_id.id,
                        'is_po_doc': True
                    })

    @api.constrains('amount_invoice', 'cut_off')
    def check_amount_equal(self):
        for record in self:
            precision_digits = 2  # Sesuaikan presisi dengan kebutuhan Anda
            precision_rounding = 0.01
        if not float_compare(record.amount_invoice, round(record.total_line),precision_digits=precision_digits) == 0 and record.cut_off !=True:
            raise UserError("Amount Invoice Harus sama dengan Total !")

    @api.onchange('bap_id')
    def _onchange_bap_id(self):
        self.po_id = False
        if self.bap_id:
            invoice_lines = []

            self.po_id = self.bap_id.po_id.id
            self.partner_id = self.bap_id.po_id.partner_id.id
            self.branch_id = self.bap_id.branch_id.id
            self.department_id = self.bap_id.department_id.id if self.bap_id.department_id else False
            self.project_id = self.bap_id.project_id.id if self.bap_id.project_id else False

            self.pph_ids = self.bap_id.pph_ids.ids
            self.total_pph = self.bap_id.total_pph
            self.pph_amount = self.bap_id.amount_pph

            if self.bap_type == 'uang muka':
                for cut_line in self.bap_id.price_cut_ids:
                    invoice_lines.append((0, 0, {
                        'product_id': cut_line.product_id.id,
                        'quantity': cut_line.qty or 1.0,
                        'price_unit': cut_line.amount,
                        'currency_id': self.currency_id.id,
                    }))
            elif self.bap_type == 'retensi':
                for cut_line in self.bap_id.price_cut_ids:
                    invoice_lines.append((0, 0, {
                        'display_type': 'product',
                        'product_id': cut_line.product_id.id,
                        'quantity': cut_line.qty or 1.0,
                        'price_unit': self.bap_id.retensi_total,
                    }))
            else:
                for bap_line in self.bap_id.bap_ids:
                    invoice_lines.append((0, 0, {
                        'display_type': 'product',
                        'product_id': bap_line.product_id.id,
                        'purchase_line_id': bap_line.purchase_line_id.id,
                        'bap_line_id': bap_line.id,
                        'picking_id': bap_line.picking_id.id,
                        'stock_move_id': bap_line.stock_move_id.id,
                        'quantity': bap_line.qty,
                        'price_unit': bap_line.unit_price,
                        'currency_id': self.currency_id.id,
                        'tax_ids': bap_line.purchase_line_id.taxes_id.ids,
                        'product_uom_id': bap_line.product_uom.id,
                        'adjustment': bap_line.adjustment,
                        'amount_adjustment': bap_line.amount_adjustment,
                    }))
            self.invoice_line_ids = invoice_lines


    def assign_todo_first(self):
        model_model = self.env['ir.model'].sudo()
        model_id = model_model.search([('model', '=', 'account.move')], limit=1)
        for res in self:
            if res.cut_off!=True:
                level=res.level
                first_user = False
                if level:
                    approval_id = self.env['wika.approval.setting'].sudo().search(
                        [ ('model_id', '=', model_id.id),('transaction_type', '!=', 'pr'),('level', '=', level)], limit=1)
                    approval_line_id = self.env['wika.approval.setting.line'].search([
                        ('sequence', '=', 1),
                        ('approval_id', '=', approval_id.id)
                    ], limit=1)
                    groups_id = approval_line_id.groups_id
                    if groups_id:
                        for x in groups_id.users:
                            if level == 'Proyek' and  res.project_id in x.project_ids:
                                first_user = x.id
                            if level == 'Divisi Operasi' and x.branch_id == res.branch_id:
                                first_user = x.id
                            if level == 'Divisi Fungsi' and x.department_id == res.department_id:
                                first_user = x.id
                    if first_user:
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': model_id.id,
                            'res_id': res.id,
                            'user_id': first_user,
                            'nomor_po': res.po_id.name,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'summary': f"Need Upload Document  {model_id.name}"
                        })
                        res.approval_stage=level
                model_model = self.env['ir.model'].sudo()
                document_setting_model = self.env['wika.document.setting'].sudo()
                model_id = model_model.search([('model', '=', 'account.move')], limit=1)
                doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

                document_list = []
                doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])
                if doc_setting_id:
                    for document_line in doc_setting_id:
                        if document_line.name != 'BAP':
                            document_list.append((0, 0, {
                                'invoice_id': res.id,
                                'document_id': document_line.id,
                                'state': 'waiting'
                            }))
                    res.document_ids = document_list
                else:
                    raise AccessError("Data dokumen tidak ada!")

    def assign_todo_first_without_activities(self):
        model_model = self.env['ir.model'].sudo()
        model_id = model_model.search([('model', '=', 'account.move')], limit=1)
        document_setting_model = self.env['wika.document.setting'].sudo()
        doc_setting_id = document_setting_model.search([
            ('model_id', '=', model_id.id),
            ('name', '=', 'Lain-lain')
        ], limit=1)
        # for res in self:
        if doc_setting_id:
            document_list = []
            for document_line in doc_setting_id:
                document_list.append((0, 0, {
                    'invoice_id': self.id,
                    'document_id': document_line.id,
                    'state': 'waiting'
                }))
            self.document_ids = document_list
        else:
            raise AccessError("Data dokumen tidak ada!")

    def submit_rejected(self, folder_id):
        facet_id = self.env['documents.facet'].sudo().search([
            ('name', '=', 'Documents'),
            ('folder_id', '=', folder_id.id)
        ], limit=1)
        for doc in self.document_ids:
            documents_model = self.env['documents.document'].sudo()
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
                    'partner_id': doc.invoice_id.partner_id.id,
                    'purchase_id': self.po_id.id,
                    'invoice_id': self.id,
                })

    
    def action_submit(self):
        for record in self:
            if any(not line.document for line in record.document_ids):
                raise ValidationError('Document belum di unggah, mohon unggah file terlebih dahulu!')
        for record in self:
            if any(line.state =='rejected' for line in record.document_ids):
                raise ValidationError('Document belum di ubah setelah reject, silahkan cek terlebih dahulu!')
        cek = False
        level=self.level
        if level:
            self.sudo().compute_account_payable()
            model_id = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu Invoice tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', 1),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            groups_id = approval_line_id.groups_id
            if groups_id:
                if self.activity_user_id.id == self._uid:
                    cek = True

        if cek:
            first_user = False
            if self.activity_ids:
                for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                    if x.user_id.id == self._uid:
                        x.status = 'approved'
                        x.action_done()
                self.state = 'uploaded'
                self.approval_stage = approval_line_id.level_role
                self.step_approve += 1
                self.env['wika.invoice.approval.line'].sudo().create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Submit Document',
                    'invoice_id': self.id
                })

                documents_model = self.env['documents.document'].sudo()
                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'Invoicing')], limit=1)
                is_continue_submit = False
                if folder_id:
                    facet_id = self.env['documents.facet'].sudo().search([
                        ('name', '=', 'Documents'),
                        ('folder_id', '=', folder_id.id)
                    ], limit=1)
                    for doc in self.document_ids.filtered(lambda x: x.state in ('uploaded','rejected')):
                        if doc.document_id.name in ['Invoice', 'Faktur Pajak']:
                            if not doc.rejected_doc_id:
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
                                        'partner_id': doc.invoice_id.partner_id.id,
                                        'purchase_id': self.po_id.id,
                                        'invoice_id': self.id,
                                    })
                        else:
                            if doc.rejected_doc_id:
                                doc.rejected_doc_id.attachment_id.write({
                                    'name': doc.filename,
                                    'datas': doc.document,
                                    'res_model': 'documents.document'
                                })
                                doc.rejected_doc_id.write({'active': True})

                groups_line = self.env['wika.approval.setting.line'].search([
                    ('level', '=', level),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                groups_id_next = groups_line.groups_id
                if groups_id_next:
                    for x in groups_id_next.users:
                        if level == 'Proyek' and self.project_id in x.project_ids:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                            first_user = x.id
                    if first_user:
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': self.env['ir.model'].sudo().search(
                                [('model', '=', 'account.move')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'nomor_po': self.po_id.name,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': """Need Approval Document Invoice"""
                        })
        else:
            raise ValidationError('User Akses Anda tidak berhak Submit!')


    def get_replace_pph_amount(self):
        _logger.info("# === GET API REPLACE PPH AMOUNT === #")
        self.ensure_one()
        url_config = self.env['wika.integration'].search([('name', '=', 'URL_INV_NON_PO')], limit=1).url
        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }

        if self.pph_amount > 0 and not self.is_upd_api_pph_amount:
            try:
                year = self.date.strftime('%Y')
                date_format = '%Y-%m-%d'
                date_from = datetime.strptime(year + '-01-01', date_format)
                date_to = datetime.strptime(year + '-12-31', date_format)
                payload = json.dumps({
                    "COMPANY_CODE": "A000",
                    "POSTING_DATE": {
                        "LOW": "%s",
                        "HIGH": "%s"
                    },
                    "DOC_NUMBER": "%s"
                }) % (str(date_from), str(date_to), self.payment_reference)
                payload = payload.replace('\n', '')

                _logger.info("# === PAYLOAD === #")
                _logger.info(payload)

                response = requests.request("GET", url_config, data=payload, headers=headers)
                result = json.loads(response.text)

                if result['DATA']:
                    _logger.info("# === RESPON DATA === #")
                    company_id = self.env.company.id
                    # diurutkan berdasarakan tahun dan doc number
                    txt_data = sorted(result['DATA'], key=lambda x: (x["YEAR"], x["DOC_NUMBER"]))
                    i = 0
                    tot_pph_amount = 0
                    for data in txt_data:
                        _logger.info(data)
                        doc_number = data["DOC_NUMBER"]
                        line_item = data["LINE_ITEM"]
                        year = str(data["YEAR"])
                        currency = data["CURRENCY"]
                        doc_type = data["DOC_TYPE"]
                        doc_date = data["DOC_DATE"]
                        posting_date = data["POSTING_DATE"]
                        pph_cbasis = data["PPH_CBASIS"] * -1
                        pph_accrual = data["PPH_ACCRUAL"] * -1
                        wht_type = data["WHT_TYPE"]

                        amount = data["AMOUNT"] * -1
                        header_text = data["HEADER_TEXT"]
                        reference = data["REFERENCE"]
                        vendor = data["VENDOR"]
                        top = data["TOP"]
                        item_text = data["ITEM_TEXT"]
                        profit_center = data["PROFIT_CENTER"]
                        name = str(doc_number) + str(year)
                        tot_pph_amount += pph_accrual

                    _logger.info('# === UPDATE ACCOUNT MOVE PPH AMOUNT === #')
                    if pph_accrual > 0 and wht_type == 'I6':
                        self.write({
                            'pph_amount': tot_pph_amount,
                            'is_upd_api_pph_amount': True
                        })
                                    
                        _logger.info(_("# === UPDATE PPH AMOUNT BERHASIL === #"))
                    else:
                        _logger.info(_("# === PPH ACCRUAL 0 === #"))

                else:
                    raise UserError(_("Data Tidak Tersedia!"))

            except Exception as e:
                _logger.info("# === EXCEPTION === #")
                _logger.info(e)
                raise UserError(_("Terjadi Kesalahan! Update Invoice Gagal."))
        else:
            raise UserError(_("Terjadi Kesalahan! pph_amount harus ada nilainya dan tidak pernah di update"))
        
    def get_dp_payment_status(self):
        self.ensure_one()
        if not self.payment_reference:
            raise UserError("Payment Reference harus diisi")

        url_config = self.env['wika.integration'].search([('name', '=', 'URL_DP_PAYMENT_STATUS')], limit=1).url
        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }

        payload = json.dumps({
            "COMPANY_CODE": "A000",
            "CLEAR_DATE": 
                {   
                    "LOW": "",
                    "HIGH":""
                },
            "DOC_NUMBER": "%s",
            "STATUS": "Y"
        }) % (self.payment_reference)
        payload = payload.replace('\n', '')
        _logger.info("# === CEK PAYLOAD === #")
        _logger.info(payload)

        # try:
        response = requests.request("GET", url_config, data=payload, headers=headers)
        txt = json.loads(response.text)

        if txt['DATA']:
            _logger.info("# === IMPORT DATA === #")
            company_id = self.env.company.id
            # _logger.info(txt['DATA'])
            txt_data = sorted(txt['DATA'], key=lambda x: x["DOC_NUMBER"])
            # txt_data = txt['DATA']
            for data in txt_data:
                # _logger.info(data)
                doc_number = data["DOC_NUMBER"]
                year = str(data["YEAR"])
                currency = str(data["CURRENCY"])
                amount = data["AMOUNT"]
                pph_cbasis = data["PPH_CBASIS"]
                ppn = data["PPN"]
                clear_date = data["CLEAR_DATE"]
                clear_doc = data["CLEAR_DOC"]
                vendor = data["VENDOR"]
                profit_center = data["PROFIT_CENTER"]
                status = data["STATUS"]

                if self.partner_id.company_id.id and self.status_payment != 'Paid':
                    self.status_payment ='Paid'

            _logger.info("# === IMPORT DATA SUKSES === #")
        else:
            raise UserError(_("Data DP Payment Status Tidak Tersedia!"))
            
    def get_payment_status(self):
        self.ensure_one()
        if self.partial_request_ids:
            self.get_payment_status_partial()
        else:
            if not self.payment_reference:
                raise UserError("Payment Reference harus diisi")

            url_config = self.env['wika.integration'].search([('name', '=', 'URL_PAYMENT_STATUS')], limit=1).url
            headers = {
                'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
                'Content-Type': 'application/json'
            }

            payload = json.dumps({
                "COMPANY_CODE": "A000",
                "CLEAR_DATE": 
                    {   
                        "LOW": "",
                        "HIGH":""
                    },
                "DOC_NUMBER": "%s"
            }) % (self.lpad_payment_reference)
            payload = payload.replace('\n', '')
            _logger.info("# === CEK PAYLOAD === #")
            _logger.info(payload)

            # try:
            response = requests.request("GET", url_config, data=payload, headers=headers)
            txt = json.loads(response.text)

            if txt['DATA']:
                _logger.info("# === IMPORT DATA === #")
                company_id = self.env.company.id
                # _logger.info(txt['DATA'])
                txt_data0 = sorted(txt['DATA'], key=lambda x: x["DOC_NUMBER"])
                txt_data = filter(lambda x: (x["STATUS"] == "X"), txt_data0)
                # txt_data = txt['DATA']
                for data in txt_data:
                    # _logger.info(data)
                    doc_number = data["DOC_NUMBER"]
                    year = str(data["YEAR"])
                    line_item = data["LINE_ITEM"]
                    amount = data["AMOUNT"]
                    clear_date = data["CLEAR_DATE"]
                    clear_doc = data["CLEAR_DOC"]
                    status = data["STATUS"]
                    new_name = doc_number+str(year)

                    if self.partner_id.company_id.id and self.status_payment != 'Paid' and year == str(self.year):
                        self.sap_amount_payment = abs(amount)
                    elif self.partner_id.company_id.id and self.status_payment != 'Paid' and year == str(self.date.year):
                        self.sap_amount_payment = abs(amount)

                _logger.info("# === IMPORT DATA SUKSES === #")
            else:
                raise UserError(_("Data Payment Status Tidak Tersedia!"))
            
    def get_payment_status_partial(self):
        _logger.info("# === get_payment_status_partial === #")
        for rec in self.partial_request_ids:
            tgl_mulai = f'{rec.year}/01/01'
            tgl_akhir = f'{rec.year}/12/31'
            doc_number = rec.lpad_no_doc_sap

            url_config = self.env['wika.integration'].search([('name', '=', 'URL_PAYMENT_STATUS')], limit=1).url
            headers = {
                'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
                'Content-Type': 'application/json'
            }

            payload = json.dumps({
                "COMPANY_CODE": "A000",
                "CLEAR_DATE": 
                    {   
                        "LOW": "%s",
                        "HIGH":"%s"
                    },
                "DOC_NUMBER": "%s"
            }) % (tgl_mulai, tgl_akhir, doc_number)
            payload = payload.replace('\n', '')
            _logger.info("# === CEK PAYLOAD === #")
            _logger.info(payload)

            try:
                response = requests.request("GET", url_config, data=payload, headers=headers)
                txt = json.loads(response.text)

                if txt['DATA']:
                    _logger.info("# === IMPORT DATA === #")
                    company_id = self.env.company.id
                    # _logger.info(txt['DATA'])
                    txt_data0 = sorted(txt['DATA'], key=lambda x: x["DOC_NUMBER"])
                    txt_data = filter(lambda x: (x["STATUS"] == "X"), txt_data0)
                    
                    # txt_data = txt['DATA']
                    for data in txt_data:
                        # _logger.info(data)
                        doc_number = data["DOC_NUMBER"]
                        year = str(data["YEAR"])
                        line_item = data["LINE_ITEM"]
                        amount = data["AMOUNT"]
                        clear_date = data["CLEAR_DATE"]
                        clear_doc = data["CLEAR_DOC"]
                        status = data["STATUS"]
                        new_name = doc_number+str(year)

                        rec.write({
                            'sap_amount_payment': abs(amount),
                            'payment_state': 'paid',
                            'accounting_doc': clear_doc
                        })
                    _logger.info("# === IMPORT DATA SUKSES === #")
                else:
                    raise UserError(_("Data Payment Status Tidak Tersedia!"))
            except Exception as e:
                    _logger.info("# === ERROR === #")
                    _logger.info(e)

    def update_journal_item_sap(self):
        _logger.info("# === GET API UPDATE JOURNAL ITEM SAP === #")
        self.ensure_one()
        url_config = self.env['wika.integration'].search([('name', '=', 'URL_INV_NON_PO')], limit=1).url
        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }

        if not self.journal_item_sap_ids:
            journal_item_sap_vals = []
            try:
                year = self.date.strftime('%Y')
                date_format = '%Y-%m-%d'
                date_from = datetime.strptime(year + '-01-01', date_format)
                date_to = datetime.strptime(year + '-12-31', date_format)
                payload = json.dumps({
                    "COMPANY_CODE": "A000",
                    "POSTING_DATE": {
                        "LOW": "%s",
                        "HIGH": "%s"
                    },
                    "DOC_NUMBER": "%s"
                }) % (str(date_from), str(date_to), self.payment_reference)
                payload = payload.replace('\n', '')

                _logger.info("# === PAYLOAD === #")
                _logger.info(payload)

                response = requests.request("GET", url_config, data=payload, headers=headers)
                result = json.loads(response.text)

                if result['DATA']:
                    _logger.info("# === RESPON DATA === #")
                    company_id = self.env.company.id
                    # diurutkan berdasarakan tahun dan doc number
                    txt_data = sorted(result['DATA'], key=lambda x: (x["YEAR"], x["DOC_NUMBER"]))
                    i = 0
                    tot_pph_amount = 0
                    for data in txt_data:
                        _logger.info(data)
                        doc_number = data["DOC_NUMBER"]
                        line_item = data["LINE_ITEM"]
                        year = str(data["YEAR"])
                        currency = data["CURRENCY"]
                        doc_type = data["DOC_TYPE"]
                        doc_date = data["DOC_DATE"]
                        posting_date = data["POSTING_DATE"]
                        pph_cbasis = data["PPH_CBASIS"] * -1
                        pph_accrual = data["PPH_ACCRUAL"] * -1
                        wht_type = data["WHT_TYPE"]

                        amount = data["AMOUNT"] * -1
                        header_text = data["HEADER_TEXT"]
                        reference = data["REFERENCE"]
                        vendor = data["VENDOR"]
                        top = data["TOP"]
                        item_text = data["ITEM_TEXT"]
                        profit_center = data["PROFIT_CENTER"]
                        name = str(doc_number) + str(year)
                        tot_pph_amount += pph_accrual

                        journal_item_sap_vals.append({
                            'invoice_id': self.id,
                            'doc_number': doc_number,
                            'amount': amount,
                            'line': line_item,
                            'project_id': self.project_id.id,
                            'branch_id': self.branch_id.id,
                            'partner_id': self.partner_id.id,
                            'po_id': self.po_id.id,
                            'status': 'not_req',
                        })

                    _logger.info('# === UPDATE JOURNAL ITEM SAP === #')
                    journal_item_sap_created = self.env['wika.account.move.journal.sap'].create(journal_item_sap_vals)

                else:
                    raise UserError(_("Data Tidak Tersedia!"))

            except Exception as e:
                _logger.info("# === EXCEPTION === #")
                _logger.info(e)
                raise UserError(_("Terjadi Kesalahan! Update Invoice Gagal."))
        else:
            raise UserError(_("Terjadi Kesalahan! Journal Item SAP sudah ada"))
        

    def action_approve(self):
        for record in self:
            if any(not line.document for line in record.document_ids):
                raise ValidationError('Document belum di unggah, mohon unggah file terlebih dahulu!')

        # self.write({'is_wizard_cancel': False})
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        documents_model = self.env['documents.document'].sudo()
        # if not self.is_upd_api_pph_amount:
        #     self.get_replace_pph_amount()

        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
        level = self.level
        is_mp = False
        if level:
            keterangan = ''
            if level == 'Proyek':
                keterangan = '''<p><strong>Dengan ini Kami Menyatakan:</strong></p>
                                <ol>
                                    <li>Bahwa Menjamin dan Bertanggung Jawab Atas Kebenaran, Keabsahan
                                    Bukti Transaksi Beserta Bukti Pendukungnya, Dan Dokumen Yang Telah Di
                                    Upload Sesuai Dengan Aslinya.</li>
                                    <li>Bahwa Mitra Kerja Tersebut telah melaksanakan pekerjaan Sebagaimana
                                    Yang Telah Dipersyaratkan di Dalam Kontrak, Sehingga Memenuhi Syarat
                                    Untuk Dibayar.</li>
                                </ol>
                                <p>Copy Dokumen Bukti Transaksi :</p>
                                <ul>
                                    <li>PO SAP</li>
                                    <li>Dokumen Kontrak Lengkap</li>
                                    <li>GR/SES</li>
                                    <li>Surat Jalan (untuk material)</li>
                                    <li>BAP</li>
                                    <li>Invoice</li>
                                    <li>Faktur Pajak</li>
                                </ul>'''
            elif level == 'Divisi Operasi':
                keterangan = '''<p>Kami Telah Melakukan Verifikasi Kelengkapan, Keabsahan Bukti Transaksi Dan Setuju Untuk Dibayarkan</p>
                                <p>Copy Dokumen Bukti Transaksi :</p>
                                <ul>
                                    <li>PO SAP</li>
                                    <li>Dokumen Kontrak Lengkap</li>
                                    <li>GR/SES</li>
                                    <li>Surat Jalan (untuk material)</li>
                                    <li>BAP</li>
                                    <li>Invoice</li>
                                    <li>Faktur Pajak</li>
                                </ul>'''
            elif level == 'Divisi Fungsi':
                keterangan = '''<p>Kami Telah Melakukan Verifikasi Kelengkapan Dokumen Dan Menyetujui Pembayaran Transaksi ini.</p>
                                <p>Copy Dokumen Bukti Transaksi :</p>
                                <ul>
                                    <li>PO SAP</li>
                                    <li>Dokumen Kontrak Lengkap</li>
                                    <li>GR/SES</li>
                                    <li>Surat Jalan (untuk material)</li>
                                    <li>BAP</li>
                                    <li>Invoice</li>
                                    <li>Faktur Pajak</li>
                                </ul>'''
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu Invoice tidak ditemukan. Silakan hubungi Administrator!')

            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            groups_id = approval_line_id.groups_id
            if groups_id:
                for x in groups_id.users:
                    if level == 'Proyek':
                        if self.project_id in x.project_ids or x.branch_id == self.branch_id or x.branch_id.parent_id.code=='Pusat':
                            if x.id == self._uid:
                                cek = True
                                is_mp = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True

        if cek == True:
            
            if is_mp == True:
                self.is_mp_approved = True

            if self.is_mp_approved:
                model_model = self.env['ir.model'].sudo()
                document_setting_model = self.env['wika.document.setting'].sudo()
                model_id = model_model.search([('model', '=', 'account.move')], limit=1)
                bap_document_setting = document_setting_model.search([('name', '=', 'BAP'), ('model_id', '=', model_id.id)], limit=1)

                # Cek apakah BAP sudah ada
                existing_bap = self.document_ids.filtered(lambda doc: doc.document_id.name == 'BAP')
                if not existing_bap and bap_document_setting:
                    document_list = [(0, 0, {
                        'invoice_id': self.id,
                        'document_id': bap_document_setting.id,
                        'state': 'waiting'
                    })]
                    self.document_ids = document_list
                elif not bap_document_setting:
                    raise AccessError("Setting dokumen BAP tidak ditemukan!")
            
                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'Invoicing')], limit=1)
                if folder_id:
                    facet_id = self.env['documents.facet'].sudo().search([
                        ('name', '=', 'Documents'),
                        ('folder_id', '=', folder_id.id)
                    ], limit=1)
                    for doc in self.document_ids.filtered(lambda x: x.state in ('uploaded', 'rejected')):
                        if doc.document_id.name == 'BAP':
                            if not doc.rejected_doc_id:
                                attachment_id = self.env['ir.attachment'].sudo().create({
                                    'name': doc.filename,
                                    'datas': doc.document,
                                    'res_model': 'documents.document'
                                })
                                if attachment_id:
                                    tag = self.env['documents.tag'].sudo().search([
                                        ('facet_id', '=', facet_id.id),
                                        ('name', '=', doc.document_id.name)
                                    ], limit=1)
                                    print("CHECK DOC BAP DI INVOICING ADA APA ENGGAK!", doc.document_id.name)
                                    # print("CHECK DOC BAP DI INVOICING ADA APA ENGGAK!", tag)
                                    existing_document = documents_model.search([('name', '=', doc.filename)], limit=1)
                                    if not existing_document:
                                        documents_model.create({
                                            'attachment_id': attachment_id.id,
                                            'folder_id': folder_id.id,
                                            'tag_ids': tag.ids,
                                            'partner_id': doc.invoice_id.partner_id.id,
                                            'purchase_id': self.po_id.id,
                                            'invoice_id': self.id,
                                        })
                        else:
                            if doc.rejected_doc_id:
                                doc.rejected_doc_id.attachment_id.write({
                                    'name': doc.filename,
                                    'datas': doc.document,
                                    'res_model': 'documents.document'
                                })
                                doc.rejected_doc_id.write({'active': True})
                    
            if approval_id.total_approve == self.step_approve:
                self.state = 'approved'
                self.approval_stage = 'Pusat'

                # replace docsss
                for doc in self.document_ids:
                    if doc.document_id.name == 'Kontrak' and doc.document:
                        for doc_po in self.po_id.document_ids:
                            bap_fname = doc.filename
                            if doc_po.document_id.name == 'Kontrak':
                                po_fname = doc_po.filename
                                if bap_fname != po_fname:
                                    doc_po.update({
                                        'document': doc.document,
                                        'filename': f'[Revised by {self.env.user.name}]' + ' ' + doc.filename,
                                        'state': 'verified'
                                    })

                    elif doc.document_id.name == 'BAP' and doc.document:
                        for doc_bap in self.bap_id.document_ids:
                            inv_fname = doc.filename
                            if doc_bap.document_id.name == 'BAP':
                                bap_fname = doc_bap.filename
                                if inv_fname != bap_fname:
                                    doc_bap.update({
                                        'document': doc.document,
                                        'filename': f'[Revised by {self.env.user.name}]' + ' ' + doc.filename,
                                        'state': 'verified'
                                    })

                    elif doc.document_id.name in ['GR', 'Surat Jalan', 'SES'] and doc.document:
                        for grses_id in self.bap_id.bap_ids:
                            for doc_grses in grses_id.picking_id.document_ids:
                                if doc_grses.state == 'rejected':
                                    if doc.picking_id.name == doc_grses.picking_id.name and doc.document_id.name == doc_grses.document_id.name:
                                        bap_fname = doc.filename
                                        grses_fname = doc_grses.filename
                                        if bap_fname != grses_fname:
                                            doc_grses.update({
                                                'document': doc.document,
                                                'filename': f'[Revised by {self.env.user.name}]' + ' ' + doc.filename,
                                                'state': 'verified'
                                            })

                for doc in self.document_ids.filtered(lambda x: x.state in ('uploaded','rejected')):
                    doc.state = 'verified'


                if self.activity_ids:
                    for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                        if x.user_id.id == self._uid:
                            print(x.status)
                            x.status = 'approved'
                            x.action_done()
                self.env['wika.invoice.approval.line'].create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Approved',
                    'invoice_id': self.id,
                    'information': keterangan if approval_line_id.check_approval else False,
                    'is_show_wizard': True if approval_line_id.check_approval else False,

                })
                if approval_line_id.check_approval:
                    action = {
                        'type': 'ir.actions.act_window',
                        'name': 'Approval Wizard',
                        'res_model': 'approval.wizard.account.move',
                        'view_type': "form",
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_keterangan': keterangan
                        },
                        'view_id': self.env.ref('wika_account_move.approval_wizard_form').id,
                    }
                    return action

            else:
                first_user = False
                # Createtodoactivity
                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level', '=', level),
                    ('sequence', '=', self.step_approve + 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                groups_id_next = groups_line_next.groups_id
                if groups_id_next:
                    for x in groups_id_next.users:
                        if level == 'Proyek' and (self.project_id in x.project_ids or x.branch_id == self.branch_id or x.branch_id.parent_id.code == 'Pusat'):
                            first_user = x.id
                        elif level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                            first_user = x.id
                        elif level == 'Divisi Fungsi' and x.department_id == self.department_id:
                            first_user = x.id
                    if first_user:
                        self.step_approve += 1
                        self.approval_stage = groups_line_next.level_role
                        print("test next approval", self.approval_stage)
                        existing_activity = self.env['mail.activity'].sudo().search([
                            ('res_model_id', '=',
                             self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1).id),
                            ('res_id', '=', self.id),
                            ('user_id', '=', first_user)
                        ])
                        if not existing_activity:
                            self.env['mail.activity'].sudo().create({
                                'activity_type_id': 4,
                                'res_model_id': self.env['ir.model'].sudo().search(
                                    [('model', '=', 'account.move')], limit=1).id,
                                'res_id': self.id,
                                'user_id': first_user,
                                'nomor_po': self.po_id.name,
                                'date_deadline': fields.Date.today() + timedelta(days=2),
                                'state': 'planned',
                                'status': 'to_approve',
                                'summary': """Need Approval Document Invoice"""
                            })

                        if self.activity_ids:
                            for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                                if x.user_id.id == self._uid:
                                    x.status = 'approved'
                                    x.action_done()
                        if self.is_wizard_cancel:
                            self.env['wika.invoice.approval.line'].create({
                                'user_id': self._uid,
                                'groups_id': groups_id.id,
                                'date': datetime.now(),
                                'note': 'Verified',
                                'invoice_id': self.id,
                                'information': keterangan if approval_line_id.check_approval else False,
                                'is_show_wizard': True if approval_line_id.check_approval else False,
                            })

                        if approval_line_id.check_approval:
                            self.baseline_date = fields.Date.today()
                            action = {
                                'type': 'ir.actions.act_window',
                                'name': 'Approval Wizard',
                                'res_model': 'approval.wizard.account.move',
                                'view_type': "form",
                                'view_mode': 'form',
                                'target': 'new',
                                'context': {
                                    'default_keterangan': keterangan
                                },
                                'view_id': self.env.ref('wika_account_move.approval_wizard_form').id,
                            }
                            return action

                    else:
                        raise ValidationError('User Role Next Approval Belum di Setting!')

        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')


    # def action_approve(self):
    #     user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
    #     documents_model = self.env['documents.document'].sudo()
    #     cek = False
    #     model_id = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
    #     level = self.level
    #     if level:
    #         keterangan = ''
    #         if level == 'Proyek':
    #             keterangan = '''<p><strong>Dengan ini Kami Menyatakan:</strong></p>
    #                             <ol>
    #                                 <li>Bahwa Menjamin dan Bertanggung Jawab Atas Kebenaran, Keabsahan
    #                                 Bukti Transaksi Beserta Bukti Pendukungnya, Dan Dokumen Yang Telah Di
    #                                 Upload Sesuai Dengan Aslinya.</li>
    #                                 <li>Bahwa Mitra Kerja Tersebut telah melaksanakan pekerjaan Sebagaimana
    #                                 Yang Telah Dipersyaratkan di Dalam Kontrak, Sehingga Memenuhi Syarat
    #                                 Untuk Dibayar.</li>
    #                             </ol>
    #                             <p>Copy Dokumen Bukti Transaksi :</p>
    #                             <ul>
    #                                 <li>PO SAP</li>
    #                                 <li>Dokumen Kontrak Lengkap</li>
    #                                 <li>GR/SES</li>
    #                                 <li>Surat Jalan (untuk material)</li>
    #                                 <li>BAP</li>
    #                                 <li>Invoice</li>
    #                                 <li>Faktur Pajak</li>
    #                             </ul>'''
    #         elif level == 'Divisi Operasi':
    #             keterangan = '''<p>Kami Telah Melakukan Verifikasi Kelengkapan, Keabsahan Bukti Transaksi Dan Setuju Untuk Dibayarkan</p>
    #                             <p>Copy Dokumen Bukti Transaksi :</p>
    #                             <ul>
    #                                 <li>PO SAP</li>
    #                                 <li>Dokumen Kontrak Lengkap</li>
    #                                 <li>GR/SES</li>
    #                                 <li>Surat Jalan (untuk material)</li>
    #                                 <li>BAP</li>
    #                                 <li>Invoice</li>
    #                                 <li>Faktur Pajak</li>
    #                             </ul>'''
    #         elif level == 'Divisi Fungsi':
    #             keterangan = '''<p>Kami Telah Melakukan Verifikasi Kelengkapan Dokumen Dan Menyetujui Pembayaran Transaksi ini.</p>
    #                             <p>Copy Dokumen Bukti Transaksi :</p>
    #                             <ul>
    #                                 <li>PO SAP</li>
    #                                 <li>Dokumen Kontrak Lengkap</li>
    #                                 <li>GR/SES</li>
    #                                 <li>Surat Jalan (untuk material)</li>
    #                                 <li>BAP</li>
    #                                 <li>Invoice</li>
    #                                 <li>Faktur Pajak</li>
    #                             </ul>'''
    #         approval_id = self.env['wika.approval.setting'].sudo().search(
    #             [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
    #         if not approval_id:
    #             raise ValidationError(
    #                 'Approval Setting untuk menu Invoice tidak ditemukan. Silakan hubungi Administrator!')

    #         approval_line_id = self.env['wika.approval.setting.line'].search([
    #             ('sequence', '=', self.step_approve),
    #             ('approval_id', '=', approval_id.id)
    #             # ('check_approval', '=', True)
    #         ], limit=1)
    #         print(approval_line_id)
    #         groups_id = approval_line_id.groups_id
    #         if groups_id:
    #             print(groups_id.name)
    #             for x in groups_id.users:
    #                 if level == 'Proyek':
    #                     if x.project_id == self.project_id or x.branch_id == self.branch_id or x.branch_id.parent_id.code=='Pusat':
    #                         if x.id == self._uid:
    #                             cek = True
    #                 if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
    #                     cek = True
    #                 if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
    #                     cek = True

    #     if cek:
    #         if approval_id.total_approve == self.step_approve:
    #             self.state = 'approved'
    #             self.approval_stage = approval_line_id.level_role

    #             keterangan = ''
    #             if level == 'Proyek':
    #                 keterangan = '''<p><strong>Dengan ini Kami Menyatakan:</strong></p>
    #                                 <ol>
    #                                     <li>Bahwa Menjamin dan Bertanggung Jawab Atas Kebenaran, Keabsahan
    #                                     Bukti Transaksi Beserta Bukti Pendukungnya, Dan Dokumen Yang Telah Di
    #                                     Upload Sesuai Dengan Aslinya.</li>
    #                                     <li>Bahwa Mitra Kerja Tersebut telah melaksanakan pekerjaan Sebagaimana
    #                                     Yang Telah Dipersyaratkan di Dalam Kontrak, Sehingga Memenuhi Syarat
    #                                     Untuk Dibayar.</li>
    #                                 </ol>
    #                                 <p>Copy Dokumen Bukti Transaksi :</p>
    #                                 <ul>
    #                                     <li>PO SAP</li>
    #                                     <li>Dokumen Kontrak Lengkap</li>
    #                                     <li>GR/SES</li>
    #                                     <li>Surat Jalan (untuk material)</li>
    #                                     <li>BAP</li>
    #                                     <li>Invoice</li>
    #                                     <li>Faktur Pajak</li>
    #                                 </ul>'''
    #             elif level == 'Divisi Operasi':
    #                 keterangan = '''<p>Kami Telah Melakukan Verifikasi Kelengkapan, Keabsahan Bukti Transaksi Dan Setuju Untuk Dibayarkan</p>
    #                                 <p>Copy Dokumen Bukti Transaksi :</p>
    #                                 <ul>
    #                                     <li>PO SAP</li>
    #                                     <li>Dokumen Kontrak Lengkap</li>
    #                                     <li>GR/SES</li>
    #                                     <li>Surat Jalan (untuk material)</li>
    #                                     <li>BAP</li>
    #                                     <li>Invoice</li>
    #                                     <li>Faktur Pajak</li>
    #                                 </ul>'''
    #             elif level == 'Divisi Fungsi':
    #                 keterangan = '''<p>Kami Telah Melakukan Verifikasi Kelengkapan Dokumen Dan Menyetujui Pembayaran Transaksi ini.</p>
    #                                 <p>Copy Dokumen Bukti Transaksi :</p>
    #                                 <ul>
    #                                     <li>PO SAP</li>
    #                                     <li>Dokumen Kontrak Lengkap</li>
    #                                     <li>GR/SES</li>
    #                                     <li>Surat Jalan (untuk material)</li>
    #                                     <li>BAP</li>
    #                                     <li>Invoice</li>
    #                                     <li>Faktur Pajak</li>
    #                                 </ul>'''
    #             self.env['wika.invoice.approval.line'].create({
    #                 'user_id': self._uid,
    #                 'groups_id': groups_id.id,
    #                 'date': datetime.now(),
    #                 'note': 'Approved',
    #                 'information': keterangan if approval_line_id.check_approval else False,
    #                 'invoice_id': self.id,
    #                 'is_show_wizard': True if approval_line_id.check_approval else False,
    #             })
    #             folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'Invoicing')], limit=1)
    #             if folder_id:
    #                 facet_id = self.env['documents.facet'].sudo().search([
    #                     ('name', '=', 'Documents'),
    #                     ('folder_id', '=', folder_id.id)
    #                 ], limit=1)
    #                 for doc in self.document_ids.filtered(lambda x: x.state in ('uploaded', 'rejected')):
    #                     doc.state = 'verified'
    #                     attachment_id = self.env['ir.attachment'].sudo().create({
    #                         'name': doc.filename,
    #                         'datas': doc.document,
    #                         'res_model': 'documents.document',
    #                     })
    #                     if attachment_id:
    #                         tag = self.env['documents.tag'].sudo().search([
    #                             ('facet_id', '=', facet_id.id),
    #                             ('name', '=', doc.document_id.name)
    #                         ], limit=1)
    #                         documents_model.create({
    #                             'attachment_id': attachment_id.id,
    #                             'folder_id': folder_id.id,
    #                             'tag_ids': tag.ids,
    #                             'partner_id': self.partner_id.id,
    #                             'purchase_id': self.bap_id.po_id.id,
    #                             'invoice_id': self.id,
    #                         })
    #             if self.activity_ids:
    #                 for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
    #                     if x.user_id.id == self._uid:
    #                         x.status = 'approved'
    #                         x.action_done()
    #             self.env['wika.invoice.approval.line'].create({
    #                 'user_id': self._uid,
    #                 'groups_id': groups_id.id,
    #                 'date': datetime.now(),
    #                 'note': 'Approved',
    #                 'invoice_id': self.id,
    #                 'information': keterangan if approval_line_id.check_approval else False,
    #             })
    #             if approval_line_id.check_approval:
    #                 print("Approval Line ID :", approval_line_id.check_approval)
    #                 action = {
    #                     'type': 'ir.actions.act_window',
    #                     'name': 'Approval Wizard',
    #                     'res_model': 'approval.wizard.account.move',
    #                     'view_type': "form",
    #                     'view_mode': 'form',
    #                     'target': 'new',
    #                     'context': {
    #                         'default_keterangan': keterangan
    #                     },
    #                     'view_id': self.env.ref('wika_account_move.approval_wizard_form').id,
    #                 }
    #                 return action

    #             if approval_line_id:
    #                 print("Approval Line ID :", approval_line_id.check_approval)
    #                 if approval_line_id.check_approval:
    #                     print("Approval Line ID :", approval_line_id.check_approval)
    #                     groups_id = approval_line_id.groups_id
    #                     if self.env.user in groups_id.mapped('users'):
    #                         action = {
    #                             'type': 'ir.actions.act_window',
    #                             'name': 'Approval Wizard',
    #                             'res_model': 'approval.wizard.account.move',
    #                             'view_type': "form",
    #                             'view_mode': 'form',
    #                             'target': 'new',
    #                             'context': {
    #                                 'default_keterangan': keterangan
    #                             },
    #                             'view_id': self.env.ref('wika_account_move.approval_wizard_form').id,
    #                         } 
    #                         return action
    #                     else:
    #                         return
    #         else:
    #             first_user = False
    #             groups_line_next = self.env['wika.approval.setting.line'].search([
    #                 ('level', '=', level),
    #                 ('sequence', '=', self.step_approve + 1),
    #                 ('approval_id', '=', approval_id.id)
    #             ], limit=1)
    #             groups_id_next = groups_line_next.groups_id
    #             if groups_id_next:
    #                 for x in groups_id_next.users:
    #                     print("ssssssssssssssssssss")
    #                     if level == 'Proyek':
    #                         if x.project_id == self.project_id or x.branch_id == self.branch_id or x.branch_id.parent_id.code == 'Pusat':
    #                             first_user = x.id
    #                     if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
    #                         first_user = x.id
    #                     if level == 'Divisi Fungsi' and x.department_id == self.department_id:
    #                         first_user = x.id

    #                 if first_user:
    #                     self.step_approve += 1
    #                     self.approval_stage = groups_line_next.level_role
    #                     self.env['mail.activity'].sudo().create({
    #                         'activity_type_id': 4,
    #                         'res_model_id': self.env['ir.model'].sudo().search(
    #                             [('model', '=', 'account.move')], limit=1).id,
    #                         'res_id': self.id,
    #                         'user_id': first_user,
    #                         'nomor_po': self.po_id.name,
    #                         'date_deadline': fields.Date.today() + timedelta(days=2),
    #                         'state': 'planned',
    #                         'status': 'to_approve',
    #                         'summary': """Need Approval Document Invoicing"""
    #                     })
    #                     keterangan = ''
    #                     if level == 'Proyek':
    #                         keterangan = '''<p><strong>Dengan ini Kami Menyatakan:</strong></p>
    #                                         <ol>
    #                                             <li>Bahwa Menjamin dan Bertanggung Jawab Atas Kebenaran, Keabsahan
    #                                             Bukti Transaksi Beserta Bukti Pendukungnya, Dan Dokumen Yang Telah Di
    #                                             Upload Sesuai Dengan Aslinya.</li>
    #                                             <li>Bahwa Mitra Kerja Tersebut telah melaksanakan pekerjaan Sebagaimana
    #                                             Yang Telah Dipersyaratkan di Dalam Kontrak, Sehingga Memenuhi Syarat
    #                                             Untuk Dibayar.</li>
    #                                         </ol>
    #                                         <p>Copy Dokumen Bukti Transaksi :</p>
    #                                         <ul>
    #                                             <li>PO SAP</li>
    #                                             <li>Dokumen Kontrak Lengkap</li>
    #                                             <li>GR/SES</li>
    #                                             <li>Surat Jalan (untuk material)</li>
    #                                             <li>BAP</li>
    #                                             <li>Invoice</li>
    #                                             <li>Faktur Pajak</li>
    #                                         </ul>'''
    #                     elif level == 'Divisi Operasi':
    #                         keterangan = '''<p>Kami Telah Melakukan Verifikasi Kelengkapan, Keabsahan Bukti Transaksi Dan Setuju Untuk Dibayarkan</p>
    #                                         <p>Copy Dokumen Bukti Transaksi :</p>
    #                                         <ul>
    #                                             <li>PO SAP</li>
    #                                             <li>Dokumen Kontrak Lengkap</li>
    #                                             <li>GR/SES</li>
    #                                             <li>Surat Jalan (untuk material)</li>
    #                                             <li>BAP</li>
    #                                             <li>Invoice</li>
    #                                             <li>Faktur Pajak</li>
    #                                         </ul>'''
    #                     elif level == 'Divisi Fungsi':
    #                         keterangan = '''<p>Kami Telah Melakukan Verifikasi Kelengkapan Dokumen Dan Menyetujui Pembayaran Transaksi ini.</p>
    #                                         <p>Copy Dokumen Bukti Transaksi :</p>
    #                                         <ul>
    #                                             <li>PO SAP</li>
    #                                             <li>Dokumen Kontrak Lengkap</li>
    #                                             <li>GR/SES</li>
    #                                             <li>Surat Jalan (untuk material)</li>
    #                                             <li>BAP</li>
    #                                             <li>Invoice</li>
    #                                             <li>Faktur Pajak</li>
    #                                         </ul>'''
    #                     self.env['wika.invoice.approval.line'].create({
    #                         'user_id': self._uid,
    #                         'groups_id': groups_id.id,
    #                         'date': datetime.now(),
    #                         'note': 'verified',
    #                         'information': keterangan if approval_line_id.check_approval else False,
    #                         'invoice_id': self.id,
    #                         'is_show_wizard': True if approval_line_id.check_approval else False,
    #                     })
    #                     if self.activity_ids:
    #                         for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
    #                             if x.user_id.id == self._uid:
    #                                 x.status = 'approved'
    #                                 x.action_done()
    #                     self.env['wika.invoice.approval.line'].create({
    #                         'user_id': self._uid,
    #                         'groups_id': groups_id.id,
    #                         'date': datetime.now(),
    #                         'note': 'Verified',
    #                         'invoice_id': self.id,
    #                         'information': keterangan if approval_line_id.check_approval else False,

    #                     })
    #                     if approval_line_id.check_approval:
    #                         print("Approval Line ID:", approval_line_id.check_approval)
    #                         action = {
    #                             'type': 'ir.actions.act_window',
    #                             'name': 'Approval Wizard',
    #                             'res_model': 'approval.wizard.account.move',
    #                             'view_type': "form",
    #                             'view_mode': 'form',
    #                             'target': 'new',
    #                             'context': {
    #                                 'default_keterangan': keterangan
    #                             },
    #                             'view_id': self.env.ref('wika_account_move.approval_wizard_form').id,
    #                         }
    #                         return action

    #                     if approval_line_id:
    #                         print("Approval Line ID:", approval_line_id.check_approval)
    #                         if approval_line_id.check_approval:
    #                             print("Approval Line ID:", approval_line_id.check_approval)
    #                             groups_id = approval_line_id.groups_id
    #                             if self.env.user in groups_id.mapped('users'):
    #                                 action = {
    #                                     'type': 'ir.actions.act_window',
    #                                     'name': 'Approval Wizard',
    #                                     'res_model': 'approval.wizard.account.move',
    #                                     'view_type': "form",
    #                                     'view_mode': 'form',
    #                                     'target': 'new',
    #                                     'context': {
    #                                         'default_keterangan': keterangan
    #                                     },
    #                                     'view_id': self.env.ref('wika_account_move.approval_wizard_form').id,
    #                                 } 
    #                                 return action
    #                             else:
    #                                 return
    #                 else:
    #                     raise ValidationError('User Role Next Approval Belum di Setting!')
    #     else:
    #         raise ValidationError('User Akses Anda tidak berhak Approve!')

    def action_reject(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        cek = False
        level = self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu Invoice tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            print(approval_line_id)
            groups_id = approval_line_id.groups_id
            if groups_id:
                if self.activity_user_id.id == self._uid:
                    cek = True
        if cek == True:
            action = {
                'name': ('Reject Reason'),
                'type': "ir.actions.act_window",
                'res_model': "reject.wizard.account.move",
                'view_type': "form",
                'target': 'new',
                'view_mode': "form",
                'context': {'groups_id': groups_id.id},
                'view_id': self.env.ref('wika_account_move.reject_wizard_form').id,
            }
            return action
        else:
            raise ValidationError('User Akses Anda tidak berhak Reject!')

    def add_pricecut_scf(self):
        action = {
            'name': ('Masukkan Nilai Amount Potongan SCF'),
            'type': "ir.actions.act_window",
            'res_model': "wika.amount.scf.wizard",
            'view_type': "form",
            'target': 'new',
            'view_mode': "form",
            # 'context': {'groups_id': groups_id.id},
            'view_id': self.env.ref('wika_account_move.view_amount_scf_price_cut_form').id,
        }
        return action

    def unlink(self):
        for record in self:
            if record.state in ('upload', 'approve'):
                raise ValidationError('Tidak dapat menghapus ketika status Vendor Bils dalam keadaan Upload atau Approve')
        return super(WikaInheritedAccountMove, self).unlink()


    def action_print_invoice(self):
        if self.level == 'Proyek':
            return self.env.ref('wika_account_move.report_wika_account_move_proyek_action').report_action(self)
        elif self.level == 'Divisi Operasi':
            return self.env.ref('wika_account_move.report_wika_account_move_divisi_action').report_action(self)
        elif self.level == 'Divisi Fungsi':
            return self.env.ref('wika_account_move.report_wika_account_move_keuangan_action').report_action(self)
        elif self.level == 'Pusat':
            return self.env.ref('wika_account_move.report_wika_account_move_keuangan_action').report_action(self)
        else:
            return super(WikaInheritedAccountMove, self).action_print_invoice()
    
    
    def compute_pph_amount(self):
        for rec in self:
            total_pph_cbasis = 0
            for line in rec.invoice_line_ids:
                total_pph_cbasis += line.pph_cash_basis
                
            rec.pph_amount += total_pph_cbasis

    def compute_amount_invoice(self):
        _logger.info("# === compute_amount_invoice === #")
        for rec in self:
            rec.amount_invoice = sum(rec.invoice_line_ids.mapped('price_subtotal'))


class WikaInvoiceDocumentLine(models.Model):
    _name = 'wika.invoice.document.line'
    _description = 'Invoice Document Line'

    invoice_id = fields.Many2one('account.move', string='Invoice ID')
    picking_id = fields.Many2one('stock.picking', string='Nomor GR/SES')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(string="Upload File", attachment=True, store=True)
    filename = fields.Char(string="File Name")
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], string='Status', default='waiting')
    rejected_doc_id = fields.Many2one('documents.document', string='Rejected Document')


    @api.onchange('document')
    def onchange_document(self):
        if self.document:
            self.check_file_size()
            self.compress_pdf()
            self.state = 'uploaded'

    def check_file_size(self):
        self.ensure_one()
        file_size = len(self.document) * 3 / 4  # base64
        if (file_size / 1024.0 / 1024.0) > 20:
            raise ValidationError(_('Tidak dapat mengunggah file lebih dari 20 MB!'))
        
    def compress_pdf(self):
        for record in self:
            try:
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
            except:
                continue

    @api.constrains('document', 'filename')
    def _check_attachment_format(self):
        for record in self:
            if record.filename and not record.filename.lower().endswith('.pdf'):
                raise ValidationError('Tidak dapat mengunggah file selain berformat PDF!')

    def write(self, values):
        _logger.info("# === WRITE DOCUMENT === #")
        record = super(WikaInvoiceDocumentLine, self).write(values)
        _logger.info(self.with_context(bin_size=True).document)
        if self.document and convertToMbSize(self.with_context(bin_size=True).document) > (1024*20):
            raise UserError('Tidak dapat mengunggah file lebih dari 20 MB!')

        return record
            
class WikaInvoiceApprovalLine(models.Model):
    _name = 'wika.invoice.approval.line'
    _description = 'Wika Approval Line'

    invoice_id = fields.Many2one('account.move', string='Invoice id')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
    information = fields.Char(string='Keterangan')
    is_show_wizard = fields.Boolean('check')

class AccountMovePriceCutList(models.Model):
    _name = 'wika.account.move.pricecut.line'

    move_id = fields.Many2one('account.move', string='Invoice')
    move_line_id = fields.Many2one('account.move.line', string='Invoice Line')
    special_gl_id = fields.Many2one('wika.special.gl', string='Special GL')
    product_id = fields.Many2one('product.product', string='Product')
    account_id = fields.Many2one('account.account', string='Account')
    percentage_amount = fields.Float(string='Percentage Amount')
    amount = fields.Float(string='Amount')
    wbs_project_definition = fields.Char(
        string='WBS Project Definition',
        compute='_compute_wbs_project_definition',
        store=True
    )
    posting_date = fields.Date(string='Posting Date')
    is_scf = fields.Boolean(string='Potongan SCF', default=False)    

    @api.depends('move_id.project_id.sap_code')
    def _compute_wbs_project_definition(self):
        for record in self:
            if record.move_id.project_id.sap_code:
                sap_code = record.move_id.project_id.sap_code
                record.wbs_project_definition = sap_code[:-1] + '-3-50-99'
            else:
                record.wbs_project_definition = False
                
    # def _compute_account_pricecut(self):
    #     move_id = self.env['account.move'].browse([self.move_id.id])
    #     if move_id:
    #         self.account_id = move_id.line_ids[0].account_id.id

class WikaAccountTax(models.Model):
    _inherit = 'account.tax'

    pph_code = fields.Char(string='PPH Code', compute='_compute_pph_code', store=True)
    is_progresif=fields.Boolean(default=False)
    @api.depends('name')
    def _compute_pph_code(self):
        for record in self:
            if record.name:
                record.pph_code = record.name[0:2]

class WikaAccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    pph_group_code = fields.Char(string='PPH Group Code', compute='_compute_pph_group_code', store=True)

    @api.depends('name')
    def _compute_pph_group_code(self):
        for record in self:
            if record.name:
                record.pph_group_code = record.name[0:2]
