from odoo import models, fields, api, exceptions,_
from odoo.exceptions import ValidationError,UserError
# from datetime import timedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar
from calendar import monthrange

class WikaPlafondBank(models.Model):
    _name = 'wika.plafond.bank'
    _description = 'Wika Plafond Bank'
    _inherit = ['mail.thread']

    nomor_kontrak = fields.Char(string='Nomor Kontrak', required=True)
    tgl_kontrak= fields.Date(string='Tanggal Kontrak', required=True)
    tipe = fields.Selection([
        ('cash', 'Cash'),
        ('non cash', 'Non Cash')
    ], string='Tipe', required=True)
    jumlah = fields.Float(string='Nilai Plafond', required=True)
    sisa = fields.Float(string='Sisa', readonly=True)
    covenant_terms = fields.Char('Covenant Terms')
    loan_cr = fields.Float(string='Loan Cr')
    loan_gearing_ratio = fields.Float(string='Loan Gearing Ratio')
    catatan = fields.Text(string='Catatan')
    nama_kontrak = fields.Char(string='Nama Kontrak', required=True)
    tgl_mulai = fields.Date(string='Tanggal Mulai', required=True)
    tgl_akhir = fields.Date(string='Tanggal Akhir', required=True)
    bank_id = fields.Many2one(comodel_name='res.bank', string= "Bank")
    terpakai = fields.Float(string='Terpakai', readonly=True)
    nilai_book = fields.Float(string='Nilai Booking', readonly=True)
    loan_der = fields.Float(string='Loan Der')
    loan_dscr = fields.Float(string='Loan Dscr')
    loan_lscr = fields.Float(string='Loan Lscr')
    total_h5 = fields.Float(string='Total H5 (Dalam Juta)', compute='compute_total', store=False)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], string='Status')
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)
    plafond_ids = fields.One2many(comodel_name='wika.loan.plafond.detail',  
        ondelete='restrict',inverse_name='plafond_id')
    Gsisa = fields.Float(related='Csisa', store=True)
    Csisa = fields.Float(string="Sisa (Dalam Miliar)", store=True, compute="_compute_sisa")
    today = fields.Date(string='Today', default=fields.Date.context_today)
    days5 = fields.Date(string='Days 5', compute='_compute_days5')

    @api.depends('today')
    def _compute_days5(self):
        for record in self:
            if record.today:
                today_formatted = datetime.strptime(record.today, '%Y-%m-%d')
                record.days5 = today_formatted + relativedelta(days=5)
            else:
                record.days5 = False

    @api.depends('sisa')
    def _compute_sisa(self):
        for rec in self:
            rec.Csisa=rec.sisa/1000000000

    def confirm(self):
        if self.jumlah:
            self.sisa =  self.jumlah - self.terpakai - self.nilai_book
        for x in self.plafond_ids:            
            x.sisa =  x.nilai - x.terpakai - x.nilai_book
        terpakai = sum(x.terpakai for x in self.plafond_ids)
        book = sum(x.nilai_book for x in self.plafond_ids)
        self.terpakai =   terpakai
        self.nilai_book =  book
        self.sisa =  self.jumlah - self.terpakai - self.nilai_book
        self.status = 'confirm'

class WikaLoanPlafondDetail(models.Model):
    _name = 'wika.loan.plafond.detail'

    plafond_id  = fields.Many2one(comodel_name='wika.plafond.bank' ,ondelete='cascade')
    jenis_id = fields.Many2one(comodel_name='wika.loan.jenis', string='Jenis', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id
    )
    tgl_mulai = fields.Date(related='plafond_id.tgl_mulai', string='Tanggal Mulai')
    nilai  = fields.Float(string='Nilai Max', required=True)
    nilai_book = fields.Float(string='Nilai Booking')
    terpakai = fields.Float(string='Terpakai', store=True, readonly=True)
    pengajuan = fields.Float(string='Pengajuan', store=True)
    sisa = fields.Float(string='Sisa Max', store=True, readonly=True)
    tgl_akhir = fields.Date(related='plafond_id.tgl_mulai', string='Tanggal Akhir')
    bank_id = fields.Many2one(related='plafond_id.bank_id', string='Bank')
    tipe = fields.Selection(related='plafond_id.tipe', string='Tipe',store=True)
    bloking_ids = fields.One2many(comodel_name='loan.plafond.bloking',inverse_name='plafond_id')
    bloking_ids = fields.One2many(comodel_name='wika.loan.plafond.bloking', inverse_name='plafond_id')

    def name_get(self):
        res = []
        for record in self:
            tit = "%s/ %s/ (%s)" % (record.plafond_id.bank_id.name,record.jenis_id.nama, record.currency_id.name)
            res.append((record.id, tit))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=1000):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            args = ['|','|',('plafond_id.bank_id.name', operator, name),('jenis_id', operator, name),('currency_id', operator, name)] + args
        categories = self.search(args, limit=limit)
        return categories.name_get()

    def action_book_view(self):
        form_id = self.env.ref('mcs_loan.plafond_bank_detail_formview_id')
        return {
            'name': 'Book Plafond',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wika.loan.plafond.detail',
            'view_id': form_id.id,
            'type': 'ir.actions.act_window',
            'res_id':self.id,
            'target': 'new',
        }

    @api.depends('nilai','sisa','terpakai','bloking_ids.jumlah')    
    def book(self):
        for x in self.bloking_ids:
            if x.jumlah:                                   
                if x.jumlah > self.nilai:
                    raise ValidationError('Total Nilai Book tidak boleh lebih dari Nilai Plafond!')                       
                self.sisa =  (self.nilai) - (self.nilai_book) -(self.terpakai)
                self.nilai_book = sum(line.jumlah for line in self.bloking_ids) 
        self.nilai_book = sum(line.jumlah for line in self.bloking_ids)  
        self.sisa =  (self.nilai) - (self.nilai_book) -(self.terpakai)
        plafond = self.env['wika.loan.plafond.detail'].search([('plafond_id', '=', self.plafond_id.id)])
        self.plafond_id.terpakai = sum(x.terpakai for x in plafond)
        self.plafond_id.nilai_book = sum(x.nilai_book for x in plafond)
        self.plafond_id.sisa =   self.plafond_id.jumlah - self.plafond_id.terpakai - self.plafond_id.nilai_book

class WikaLoanPlafondBlocking(models.Model):
    _name = 'wika.loan.plafond.bloking'
    _description = 'Loan Plafond Bloking'

    plafond_id = fields.Many2one(comodel_name='wika.loan.plafond.detail',string='Plafond')
    department_id = fields.Many2one(comodel_name='hr.department',string='Divisi Lama')
    branch_id = fields.Many2one(comodel_name='res.branch', string='Divisi')
    proyek_id = fields.Many2one(comodel_name='wika.project',string='Proyek')

    jenis_id = fields.Many2one(related='plafond_id.jenis_id',string='Jenis')
    bank_id = fields.Many2one(related='plafond_id.bank_id',string='Bank')
    jumlah = fields.Float(string='Jumlah Bloking')

    def update_branch(self):
        ncl=self.env['wika.loan.plafond.bloking'].search([])
        for x in ncl:
            branch=self.env['res.branch'].search([('code','=',x.department_id.code)],limit=1)
            x.branch_id=branch.id
    
    
        