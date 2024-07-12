from odoo import api, fields, models, _
from datetime import datetime, timedelta

class WikaNonCashLoan(models.Model):
    _name = 'wika.noncash.loan'
    _description = 'Non Cash Loan'
    # _inherit = 'mail.thread'
    _order = 'sisa_outstanding desc'

    plaf_id = fields.Many2one('wika.plafond.bank', string="Plafond Bank")
    name = fields.Char(string='Nomor', required=True, copy=False, readonly=True, 
        index=True, default=lambda self: _('New'))
    no_swift = fields.Char(string='Nomor Swift',copy=False)   
    plafond_bank_id = fields.Many2one(comodel_name='wika.loan.plafond.detail',
        string="Plafond", ondelete='set null', index=True)
    vendor_id = fields.Many2one(comodel_name='res.partner',
        string="Vendor/Owner", ondelete='set null', index=True)  
    tgl_mulai = fields.Date(string='Tanggal Mulai')
    tgl_akhir = fields.Date(string='Tanggal Akhir')
    branch_id = fields.Many2one(comodel_name='res.branch', index=True, string='Divisi')
    jumlah_pengajuan = fields.Float(string='Nilai Pengajuan', index=True)
    jumlah_pengajuan_asing = fields.Float(string='Nilai Pengajuan Asing', copy=False)
    dalam_proses = fields.Float(string='Dalam Proses', default=0, copy=False)
    sisa_outstanding = fields.Float(string='Outstanding', default=0, copy=False)
    stage_id = fields.Many2one(comodel_name='wika.loan.stage', domain=[('tipe','=','Non Cash'),
        ],string='Status', copy=False, track_visibility='onchange', index=True)
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency')
    stage_name = fields.Char(related='stage_id.name', string='Status Name', store=True, index=True)
    bank_id = fields.Many2one(comodel_name='res.bank', string="Bank", index=True)
    jenis_id = fields.Many2one(comodel_name='wika.loan.jenis',
        string="Kriteria", required=True)
    projek_id = fields.Many2one(comodel_name='project.project', string="Proyek")
    partner_jo = fields.Char(string='Partner JO')
    nama_proyek = fields.Char(string='Nama Proyek')
    tgl_pembukaan = fields.Date(string='Tanggal Pembukaan', required="True", index=True,
        default=datetime.today())  
     
    nama_jenis = fields.Char(string="Nama Kriteria", index=True)
    no_rekening = fields.Many2one(comodel_name='res.partner.bank',
        string="No Rekening", index=True)
    # department_id   = fields.Many2one(comodel_name='hr.department',
    #                           string="Divisi")
    # audit_log_ids = fields.One2many(comodel_name='wika.ncl.audit.log', inverse_name='ncl_id')
    tgl_mulai_perkiraan = fields.Date(string='Tanggal Mulai Perkiraan')
    # tgl_akhir_perkiraan = fields.Date(string='Tanggal Akhir Perkiraan')
    # tgl_akseptasi   = fields.Date(string='Tanggal Akseptasi')
    # rate_bunga      = fields.Float(string='Rate Bunga (%)')
    # total_bunga     = fields.Float(
    #                         compute='_cal_amount_all',
    #                         string='Nominal Bunga',
    #                         store=True
    #                         )
    #                      )
    # stage_id1       = fields.Many2one(related='stage_id',store=False)
    # stage_id2       = fields.Many2one(related='stage_id',store=False)
    

    tipe_jenis = fields.Many2one(string='Tipe Kriteria', comodel_name='wika.tipe.jenis')                    
    tipe_jenis_name = fields.Char(related='tipe_jenis.name')
    catatan = fields.Text(string='Catatan') 
    # tgl_swift                   = fields.Date(string='Tanggal Swift',copy=False)
    # payment_ids                 = fields.One2many(comodel_name='ncl.pembayaran', string="Rencana Pembayaran",
    #                               inverse_name='loan_id', ondelete='cascade', index="true",copy=False)
    # payment_ids2                 = fields.One2many(comodel_name='ncl.pembayaran', string="Rencana Pembayaran",
    #                               inverse_name='loan_id', ondelete='cascade', index="true",copy=False)
    # payment_ids3 = fields.One2many(comodel_name='ncl.pembayaran', string="Rencana Pembayaran",
    #                                inverse_name='loan_id', ondelete='cascade', index="true", copy=False)
    # payment_ids4 = fields.One2many(comodel_name='ncl.pembayaran', string="Rencana Pembayaran",
    #                                inverse_name='loan_id', ondelete='cascade', index="true", copy=False)
    # payment_id                  = fields.Many2one('ncl.pembayaran',string='Pembayaran',copy=False)
    # total_pokok                 = fields.Float(string='Total Pokok', compute='_compute_total',copy=False)
    # total_bunga                 = fields.Float(string='Total Bunga', compute='_compute_total',copy=False)
    anak_perusahaan = fields.Boolean(related='branch_id.anak_perusahaan',store=False)
    department_parent = fields.Many2one(related='branch_id.parent_id',store=False)
    nama_vendor = fields.Char(string='Nama Vendor/Owner')
    nama_nasabah = fields.Char(string='Nama Nasabah') 
    masa_klaim = fields.Integer(string='Masa Klaim (Hari)')
    tgl_jatuh_tempo = fields.Date(string='Tanggal Jatuh Tempo')
    # payment_keterangan          = fields.Char(related='payment_id.keterangan',string='Keterangan Bayar',copy=False)
    # tgl_bayar                   = fields.Date(related='payment_id.tgl_bayar',string='Tanggal Bayar',copy=False)
    kurs                        = fields.Float(string='Kurs')                    
    nomor_surat = fields.Char(string='Nomor Surat')
    tenor = fields.Integer(string='Tenor Hari')
    sejak = fields.Char(string='Terhitung Sejak') 
    sisa_plafond = fields.Float(related='plafond_bank_id.plafond_id.sisa', string='Sisa Plafond')
    sisa_plafond_max = fields.Float(related='plafond_bank_id.sisa', string='Sisa Plafond Max')
    # plaf_id                     = fields.Many2one(related='plafond_bank_id.plafond_id',store=True)
    company_currency = fields.Many2one(string='Currency', comodel_name="res.currency")

    # status_loan = fields.Selection(string="Status Aktif Loan", selection=[
    #     ('Aktif', 'Aktif'),
    #     ('Tidak Aktif', 'Tidak Aktif')], default='Aktif',copy=False)
    # keterangan_hari_mulai       = fields.Char(string="Keterangan Hari Mulai", store=True)
    # keterangan_hari_akhir       = fields.Char(string="Keterangan Hari Akhir", store=True)

    # amandemen_ids               = fields.One2many(comodel_name='loan.amandemen', string="History Amandemen",
    #                               inverse_name='loan_id', ondelete='cascade', index="true",copy=False)
    # amandemen_ke                = fields.Integer(string='Amandemen Ke', default=0,copy=False)
    # jumlah_pengajuan_baru       = fields.Float(string='Nilai Pengajuan')
    # jumlah_pengajuan_asing_baru = fields.Float(string='Nilai Pengajuan Asing')
    # kurs_baru                   = fields.Float(string='Kurs')
    # tgl_mulai_baru              = fields.Date(string='Tanggal Mulai')
    # tgl_akhir_baru              = fields.Date(string='Tanggal Akhir')
    # comp_amandemen              = fields.Integer(string='Amandemen Ke', compute='_compute_amandemen',copy=False)
    # tgl_jatuh_tempo_baru = fields.Date(string='Tanggal Jatuh Tempo')
    # keterangan_hari_mulai_baru       = fields.Char(string="Keterangan Hari Mulai", store=True)
    # keterangan_hari_akhir_baru       = fields.Char(string="Keterangan Hari Akhir", store=True)
    # catatan_sistem                   = fields.Text(string="Catatan Sistem")



    jenis_nasabah = fields.Selection([
        ('SUPPLIER', 'Supplier'),
        ('SUBKONT', 'Subkon')
    ], string='Jenis Nasabah')
    nomor_bukti = fields.Char('Nomor Bukti')
    nomor_kontrak = fields.Char('Nomor Kontrak')
    # nama_barang = fields.Char('Nama Barang')
    tanggal_kontrak = fields.Date('Tanggal Kontrak')
    nilai_pokok_tagihan = fields.Float('Nilai Pokok Tagihan')
    ppn = fields.Float('PPN')
    nilai_pokok_ppn = fields.Float('Nilai Pokok + PPN')
    potongan_pph_persen = fields.Float('Potongan PPH (%)')
    potongan_pph = fields.Float('Potongan PPH (Rp)')
    potongan_lain = fields.Float('Potongan Lain')
    nilai_tagihan_netto = fields.Float('Nilai Tagihan Netto')
    # nilai_progress = fields.Float('Nilai Progress')
    # potongan_um = fields.Float('Potongan Uang Muka')
    # is_pmcs = fields.Boolean(string="Dari PMCS", default=False)

    # default_debit_acc = fields.Many2one(comodel_name='account.account', string="Default Debit Account",
    #                                     domain="[('user_type_id','=',1)]")
    # default_credit_acc = fields.Many2one(comodel_name='account.account', string="Default Credit Account",
    #                                      domain="[('user_type_id','=',2)]")

    invoice_id = fields.Many2one(string="Invoice", comodel_name='account.move')
    # move_id = fields.Many2one(string="Journal Entry", comodel_name='account.move')
    # active = fields.Boolean('Active',
    #                         help="If the active field is set to False, it will allow you to hide the account without removing it.",
    #                         default=True)

# class WikAuditLog(models.Model):
#     _name = 'wika.ncl.audit.log'
#     _description = 'Audit Log'

#     user_id = fields.Many2one(comodel_name='res.users',string='User')
#     groups_id = fields.Many2one(comodel_name='res.groups',string='Group')
#     date = fields.Datetime(string='Date')
#     description = fields.Char(string='Description')
#     level = fields.Char(string='Level')
#     ncl_id = fields.Many2one(comodel_name='wika.noncash.loan')

class WikaNclPembayaran(models.Model):
    _name = 'wika.ncl.pembayaran' 
    _description = 'Non Cash Loan Pembayaran'
    _rec_name = 'loan_id' 
    _inherit = 'mail.thread'
    _order  = 'state asc, id desc'
    
    loan_id = fields.Many2one(comodel_name='wika.noncash.loan', string="Loan",
        ondelete='set null')
    # jenis_id                = fields.Many2one(related='loan_id.jenis_id')
    nama_jenis              = fields.Char(related='loan_id.nama_jenis',string="Kriteria",store=True, index=True)
    # nama_tipe_kriteria      = fields.Char(related='loan_id.tipe_jenis_name',string="Tipe Kriteria",store=True)
    jumlah_pengajuan        = fields.Float(related='loan_id.jumlah_pengajuan', string="Nilai Pengajuan",
                                           store = True,group_operator = 'avg')
    plafond_bank_id         = fields.Many2one(related='loan_id.plafond_bank_id', string="Plafond Bank", store=True)
    vendor_id               = fields.Many2one(related='loan_id.vendor_id',string="Vendor") 
    nomor_swift = fields.Char(related='loan_id.no_swift',string="Nomor Swift",store=True) 
    # stage_name              = fields.Char(related='loan_id.stage_name',string="Stage Name",store=True) 
    no_swift_akseptasi      = fields.Char(string='Nomor Swift Akseptasi')   
    tgl_swift_akseptasi     = fields.Date(string='Tanggal Swift Akseptasi')
    no_swift_tr             = fields.Char(string='Nomor Swift TR/Perpanjangan')
    tgl_swift_tr            = fields.Date(string='Tanggal Swift TR/Perpanjangan')
    # no_swift_tr_baru        = fields.Char(string='Nomor Swift TR/Perpanjangan')
    # tgl_swift_tr_baru       = fields.Date(string='Tanggal Swift TR/Perpanjangan')
    bank_id                 = fields.Many2one(related='loan_id.bank_id',string="Bank", index=True, store=True)
    # department_id           = fields.Many2one(related='loan_id.department_id',
    #                           string="Divisi Lama", store=True, index=True, readonly=True)
    branch_id               = fields.Many2one(related='loan_id.branch_id',
                              string="Divisi", store=True, index=True, readonly=True)
    # company_currency        = fields.Many2one(related='loan_id.company_currency',
    #                                           string='Currency')
    currency_id             = fields.Many2one(related='loan_id.currency_id',
                                              string='Currency',store=True)
    # currency_diff           = fields.Many2one(comodel_name="res.currency",string='Currency') 
    kurs_awal               = fields.Float(related='loan_id.kurs',string='Kurs Pembukaan')    
    kurs_baru               = fields.Float(string='Kurs Baru')  
    # masa_klaim              = fields.Integer(string='Masa Klaim (Hari)')

    # cur_id                  = fields.Integer(related='loan_id.currency_id.id',store=False)
    nilai_pokok_asing       = fields.Float(string='Pembayaran Pokok Asing')

    nilai_pokok             = fields.Float(string='Pembayaran Pokok')
    nilai_bunga             = fields.Float(string='Nilai Bunga')
    total                   = fields.Float(string='Total', compute='_compute_total', store=True)
    # jumlah_bayar            = fields.Float(string='Jumlah Bayar')

    tgl_jatuh_tempo         = fields.Date(string='Tanggal Jatuh Tempo', index=True, required=True)
    # tgl_bayar               = fields.Date(string='Tanggal Bayar')
    keterangan              = fields.Char(string='Ket')
    state = fields.Selection(string='Status', selection=[
        ('Belum Dibayar', 'Belum Dibayar'),
        ('Lunas', 'Lunas'),
        ('TR', 'TR'),
        ('Perpanjangan', 'Perpanjangan')
    ], default='Belum Dibayar', index=True)
    # cek_pelunasan           = fields.Boolean(string='Apakah Pelunasan dilakukan dengan Bank Lain?')
    # new_no_rekening = fields.Many2one(comodel_name='res.partner.bank',
    #                               string="No Rekening")
    # new_bank_id             = fields.Many2one(comodel_name='res.bank',string='New Bank')
    # new_plafond_id          = fields.Many2one(comodel_name='loan.plafond.detail')
    status_akseptasi        = fields.Selection(string='Status Akseptasi', selection=[
                                ('Akseptasi', 'Akseptasi'),
                                ('Tidak Akseptasi', 'Tidak Akseptasi')])            
    # projek_id               = fields.Many2one(comodel_name='wika.project',
    #                                       string="Proyek", ondelete='set null', index=True)

    # nomor_swift_baru = fields.Char(string="Nomor Swift Baru", store=True)
    # tgl_swift_baru = fields.Date(string='Tanggal Swift Baru', store=True)
    # tgl_jatuh_tempo_baru = fields.Date(string='Tanggal Jatuh Tempo Baru', store=True)
    keterangan_jatuh_tempo = fields.Selection(string='Keterangan Jatuh Tempo',
                                              selection=[('pasti', 'Pasti'), ('tidak_pasti', 'Tidak Pasti')])
    # # Baru
    # tgl_skrg   = fields.Date(string='Tanggal skrg', store=True)
    # # total_h5=fields.Float(string='Total H-5 (Dalam Juta)',compute='compute_total', store=True)
    
    # plaf_id     = fields.Many2one(related='plafond_bank_id.plafond_id',store=True)
    plaf_id     = fields.Many2one('wika.plafond.bank',store=True)
    # Csisa       = fields.Float(string="Total (Dalam Juta)",store=True,compute="_compute_sisa")
    # Gsisa       = fields.Float(related='Csisa', store=True)
    # status_comdisc = fields.Selection(string="COMP/DISC", selection=[
    #     ('Comply', 'Comply'),
    #     ('Discrepency', 'Discrepency')])
    sel_over= fields.Selection(selection=[
        ('Toleransi', 'Toleransi'),
        ('Overdraft', 'Overdraft')])
    tr_ids = fields.One2many(comodel_name='wika.loan.log.tr', string="History TR",
        inverse_name='pembayaran_id', ondelete='cascade', index="true", copy=False)
    nomor_memorial = fields.Char('Nomor Memorial')
    no_sap = fields.Char('No Doc SAP')
    payment_proposal_id_sap              = fields.Char(string='Payment Proposal Id SAP')
    line_item_sap = fields.Char(string='Line Item SAP')
    fiscal_year_sap = fields.Char(string='Fiscal Year SAP')

class WikaLogTr(models.Model):
    _name ='wika.loan.log.tr'

    ke = fields.Integer(string='Ke')
    pembayaran_id = fields.Many2one(comodel_name='wika.ncl.pembayaran', string="Loan Pembayaran",
        ondelete='cascade')
    loan_id = fields.Many2one(related='pembayaran_id.loan_id', store=True)
    no_swift_lama = fields.Char(string="Nomor Swift TR")
    tgl_eksekusi = fields.Date(string='Tanggal Eksekusi')
    tgl_swift_lama = fields.Date(string='Tanggal Swift TR')
    tgl_jatuh_tempo_lama = fields.Date(string='Tanggal Jatuh Tempo')
    