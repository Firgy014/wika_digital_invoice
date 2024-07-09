from odoo import api, fields, models, _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class WikaCashLoan(models.Model):
    _name = 'wika.cash.loan'
    _description = 'Cash Loan'
    _inherit = 'mail.thread'
    _order = 'id desc'

    # @api.model
    # def _default_stage(self):
    #     return self.env['loan.stage'].search(
    #         [('sequence', '=', 1),('tipe', '=', 'Cash')],limit=1)
    # @api.model
    # def _default_company(self):
    #     return self.env['res.currency'].search(
    #         [('id', '=', 13)],limit=1)
    # @api.model
    # def _default_currency(self):
    #     return self.env['res.currency'].search(
    #         [('name', '=', 'IDR')],limit=1)
        
    name = fields.Char(string='Nomor', required=True, copy=False,
        readonly=True, index=True, default=lambda self: _('New'))
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)
    bank_id = fields.Many2one(comodel_name='res.bank',
        string="Bank", required=True)    
    jenis_id = fields.Many2one(comodel_name='wika.loan.jenis',
        string="Kriteria")
    tgl_mulai = fields.Date(string='Tanggal Mulai')
    tgl_akhir = fields.Date(string='Tanggal Akhir')
    ket_alokasi = fields.Text(string='Keterangan Alokasi', required=True)
    nomor_surat = fields.Char(string='Nomor Surat')
    tenor = fields.Integer(string='Tenor Bulan')
    sejak = fields.Char(string='Terhitung Sejak') 
    tgl_perpanjangan  = fields.Date(string='Tanggal Perpanjangan')  
    currency_id  = fields.Many2one(comodel_name='res.currency',
        string='Currency')
    no_rekening = fields.Many2one(comodel_name='res.partner.bank',
        string="No Rekening")
    plafond_bank_id  = fields.Many2one(comodel_name='wika.loan.plafond.detail',
        string="Plafond", ondelete='set null', index=True)
    nilai_pengajuan = fields.Float(string='Nilai Pengajuan')
    rate_bunga= fields.Float(string='Suku Bunga (%)')
    catatan = fields.Text(string='Catatan')
    kurs = fields.Float(string='Kurs')                    
    tgl_pengajuan = fields.Date(string='Tanggal Pengajuan', required="True",
        default=datetime.today())  
    stage_id = fields.Many2one(comodel_name='wika.loan.stage', 
        domain=[('tipe','=','Cash'), ('name','not in', ['Ditolak','Cancel','Perpanjangan'])], 
        string='Status', copy=False)
    payment_ids = fields.One2many(comodel_name='wika.cl.payment', string="Rencana Pembayaran",
        inverse_name='cash_loan_id', ondelete='cascade', index="true",copy=False)
    stage_name  = fields.Char(related='stage_id.name' ,string='Status Name',store=True) 
    sisa_pengajuan = fields.Float(string='Outstanding')
    # company_id        = fields.Many2one(comodel_name='res.company', string='Perusahaan', required=True,
    #                                   default=lambda self: self.env['res.company']._company_default_get('cash.loan'))
  
    # tgl_pencairan   = fields.Date(string='Tanggal Pencairan')
    # nilai_pengajuan_asing = fields.Float(string='Nilai Pengajuan Asing')
    # company_currency = fields.Many2one(string='Currency', default=_default_company, comodel_name="res.currency")

    # sisa_pokok      = fields.Float(string='Sisa Pokok',compute='_compute_total')
    # sisa_bunga      = fields.Float(string='Sisa Bunga',compute='_compute_total')
    # total_sisa      = fields.Float(string='Total Sisa')
    # plaf_id = fields.Many2one(related='plafond_bank_id.plafond_id',store=True)
    plaf_id = fields.Many2one('wika.plafond.bank', string="Plafond Bank")

class WikaCashLoanPembayaran(models.Model):
    _name = 'wika.cl.payment' 
    _description = 'Cash Loan Pembayaran'
    _rec_name = 'cash_loan_id' 
    _inherit = 'mail.thread'
    _order  = 'state asc,id desc'

    # @api.model
    # def _default_currency(self):
    #     return self.env['res.currency'].search(
    #         [('name', '=', 'IDR')],limit=1)

    cash_loan_id = fields.Many2one(comodel_name='wika.cash.loan', string="Loan",
        ondelete='set null')
    tenor = fields.Integer(related='cash_loan_id.tenor', string='Tenor Bulan')
    tgl_jatuh_tempo = fields.Date(string='Tanggal Jatuh Tempo', required=True)
    rate_bunga = fields.Float(string='Rate Bunga')
    nilai_pokok_asing = fields.Float(string='Pembayaran Pokok Asing')
    nilai_bunga_asing = fields.Float(string='Nilai Bunga Asing')
    currency_id = fields.Many2one(related='cash_loan_id.currency_id',
        string='Currency',store=True)
    nilai_pokok = fields.Float(string='Pembayaran Pokok', required=True)
    state = fields.Selection(string='Status', selection=[
        ('Belum Dibayar', 'Belum Dibayar'),
        ('Lunas', 'Lunas'),
        ('Perpanjangan', 'Perpanjangan') 
        ], default='Belum Dibayar')
    keterangan = fields.Char(string='Keterangan')
    nilai_bunga = fields.Float(string='Nilai Bunga', required=True)
    jumlah_bayar = fields.Float(string='Jumlah Bayar')
    total = fields.Float(string='Total', store=True)
    nilai_pengajuan = fields.Float(related='cash_loan_id.nilai_pengajuan', string="Nilai Pengajuan")
    plafond_bank_id     = fields.Many2one(related='cash_loan_id.plafond_bank_id', string="Plafond Bank", store=True)
    bank_id             = fields.Many2one(related='cash_loan_id.bank_id', string="Bank", store=True)
    Csisa = fields.Float(string="Total (Dalam Juta)", store=True)
    # rate_bunga_new     = fields.Float(string='Rate Bunga Baru')
    # nilai_bunga_new     = fields.Float(string='Pembayaran Bunga Baru')
    # nilai_bunga_asing_new     = fields.Float(string='Pembayaran Bunga Asing Baru')


    # company_currency    = fields.Many2one(related='loan_id.company_currency',
    #                      string='Currency',store=True
    #                      )
    # currency_new        = fields.Many2one(comodel_name='res.currency',
    #                      string='New Currency'
    #                      )
    # kurs_awal           = fields.Float(related='loan_id.kurs',string='Kurs Pembukaan')    
    # tgl_jatuh_tempo_new = fields.Date(string='Tanggal Jatuh Tempo')

    # tgl_bayar           = fields.Date(string='Tanggal Bayar',default=datetime.today())
    # selisih_bayar       = fields.Float(compute='_compute_selisih', readonly=True)
   
    
    # tipe_bayar          = fields.Boolean(string='Apakah sisanya akan di perpanjang?',default=False)

    # # Baru
    plaf_id = fields.Many2one('wika.plafond.bank', string="Plafond Bank")

    # plaf_id     = fields.Many2one(related='plafond_bank_id.plafond_id',store=True)
    # Gsisa       = fields.Float(related='Csisa', store=True)
    # perpanjangan_ids      = fields.One2many(comodel_name='loan.log.perpanjangan', string="History Perpanjangan",
    #                          inverse_name='pembayaran_id', ondelete='cascade', index="true", copy=False)
