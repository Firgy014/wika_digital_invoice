from odoo import api, fields, models, _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class WikaCashLoan(models.Model):
    _name = 'wika.cash.loan'
    _description = 'Cash Loan'
    _inherit = 'mail.thread'
    _order = 'id desc'
    
    @api.model
    def _default_stage(self):
        return self.env['wika.loan.stage'].search(
            [('sequence', '=', 1),('tipe', '=', 'Cash')],limit=1)
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
        string="Bank")    
    jenis_id = fields.Many2one(comodel_name='wika.loan.jenis',
        string="Kriteria")
    tgl_mulai = fields.Date(string='Tanggal Mulai')
    tgl_akhir = fields.Date(string='Tanggal Akhir')
    ket_alokasi = fields.Text(string='Keterangan Alokasi', required=True)
    nomor_surat = fields.Char(string='Nomor Surat')
    tenor = fields.Integer(string='Tenor Bulan')
    sejak = fields.Char(string='Terhitung Sejak') 
    tgl_perpanjangan  = fields.Date(string='Tanggal Perpanjangan') 
    currency_id = fields.Many2one('res.currency', 
        default=lambda self: self.env['res.currency'].search([('name', '=', 'IDR')]).id, string='Currency')
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
        string='Status', copy=False, default=_default_stage)
    payment_ids = fields.One2many(comodel_name='wika.cl.payment', string="Rencana Pembayaran",
        inverse_name='cash_loan_id', ondelete='cascade', index="true",copy=False)
    stage_name  = fields.Char(related='stage_id.name' ,string='Status Name',store=True) 
    sisa_pengajuan = fields.Float(string='Outstanding', compute='_compute_sisa')
    plaf_id = fields.Many2one(
        comodel_name='wika.plafond.bank', 
        string="Plafond ID", 
        related='plafond_bank_id.plafond_id', 
        store=True
    )
    # company_id        = fields.Many2one(comodel_name='res.company', string='Perusahaan', required=True,
    #                                   default=lambda self: self.env['res.company']._company_default_get('cash.loan'))
  
    tgl_pencairan   = fields.Date(string='Tanggal Pencairan')
    nilai_pengajuan_asing = fields.Float(string='Nilai Pengajuan Asing')
    # company_currency = fields.Many2one(string='Currency', default=_default_company, comodel_name="res.currency")

    sisa_pokok      = fields.Float(string='Sisa Pokok',compute='_compute_total')
    sisa_bunga      = fields.Float(string='Sisa Bunga',compute='_compute_total')
    # total_sisa      = fields.Float(string='Total Sisa')
    # plaf_id = fields.Many2one(related='plafond_bank_id.plafond_id',store=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('wika.cash.loan') or  _('New')
        result = super(WikaCashLoan, self).create(vals)
        return result   

    def request(self):        
        stage_sekarang = self.stage_id.sequence
        stage_next = self.env['wika.loan.stage'].search([('sequence','=',stage_sekarang+1),
            ('tipe','=','Cash')])
        if stage_next.id:
            self.stage_id = stage_next.id
    
    def approve(self):
        plafond = self.env['wika.loan.plafond.detail'].search([('id', '=', self.plafond_bank_id.id)])

        stage_sekarang = self.stage_id.sequence
        stage_next = self.env['wika.loan.stage'].search([('sequence','=',stage_sekarang+1),
            ('tipe','=','Cash'),
            ('name','=','Disetujui')])
        if stage_next.id:
            for data in plafond:                
                use = sum(x.nilai_pengajuan for x in self)
                plafond.terpakai = plafond.terpakai+float(use)
                plafond.sisa = plafond.nilai - plafond.nilai_book - plafond.terpakai
                plafond.plafond_id.terpakai = sum(x.terpakai for x in plafond.plafond_id.plafond_ids)                   
                plafond.plafond_id.sisa = plafond.plafond_id.jumlah - plafond.plafond_id.terpakai - plafond.plafond_id.nilai_book
            self.stage_id = stage_next.id    

    def notapprove(self):        
        stage_sekarang = self.stage_id.sequence
        stage_next = self.env['wika.loan.stage'].search([('sequence','=',stage_sekarang+1),
            ('tipe','=','Cash'),
            ('name','=','Ditolak')])
        if stage_next.id:
            self.stage_id = stage_next.id

    def penarikan(self):
        loan = self.env['wika.cash.loan'].search([('plafond_bank_id', '=', self.plafond_bank_id.id)])

        stage_sekarang = self.stage_id.sequence
        stage_next = self.env['wika.loan.stage'].search([('sequence','=',stage_sekarang+1),
            ('tipe','=','Cash'),
            ('name','=','Penarikan')])
        
        today = fields.Date.context_today(self)

        if stage_next:
            self.stage_id = stage_next.id
            self.tgl_pencairan = today

    def cancel(self):
        plafond = self.env['wika.loan.plafond.detail'].search([('id', '=', self.plafond_bank_id.id)])
        stage_next = self.env['wika.loan.stage'].search([
            ('tipe', '=', 'Cash'),
            ('name', '=', 'Cancel')])
        payment_pembayaran = self.env['wika.cl.payment'].search([
            ('cash_loan_id', '=', self.id),
            ('state', '=', 'Lunas')])

        if payment_pembayaran:
            raise ValidationError('Rincian Anda sudah Lunas, Data tidak bisa dibatalkan!')
        else:
            for data in plafond:
                use = sum(x.nilai_pengajuan for x in self)
                data.terpakai = data.terpakai - float(use)
                data.sisa = data.nilai - data.terpakai - data.nilai_book
            plafond.plafond_id.terpakai = sum(x.terpakai for x in self.plafond_bank_id.plafond_id.plafond_ids)
            plafond.plafond_id.sisa = plafond.plafond_id.jumlah - plafond.plafond_id.terpakai - plafond.plafond_id.nilai_book
            self.stage_id = stage_next.id
            self.payment_ids.unlink()

    def lunas_auto(self):
        today = fields.Date.today()                    
        cl_tempo = self.env['wika.cl.payment'].search([
            ('state','=','Belum Dibayar'),
            ('tgl_jatuh_tempo','<',today)
        ])
        for x in cl_tempo:
            if cl_tempo:
                x.plafond_bank_id.terpakai = x.plafond_bank_id.terpakai - x.cash_loan_id.nilai_pengajuan               
                x.plafond_bank_id.sisa = x.plafond_bank_id.nilai - x.plafond_bank_id.terpakai
                x.plafond_bank_id.plafond_id.terpakai = x.plafond_bank_id.plafond_id.terpakai - x.nilai_pokok              
                x.plafond_bank_id.plafond_id.sisa = x.plafond_bank_id.plafond_id.jumlah - x.plafond_bank_id.plafond_id.terpakai  - x.plafond_bank_id.plafond_id.nilai_book       
        
                x.state = 'Lunas'
                x.keterangan = 'Auto Payment'
                x.tgl_bayar  = today

    @api.depends('payment_ids.nilai_pokok', 'payment_ids.nilai_bunga')
    def _compute_total(self):
        for record in self:
            record.sisa_pokok = sum(line.nilai_pokok for line in record.payment_ids)
            record.sisa_bunga = sum(line.nilai_bunga for line in record.payment_ids)
            #if record.jumlah_bayar > record.nilai_pengajuan:
                #raise Warning('Total Bayar tidak boleh lebih dari Nilai Pengajuan!')

    @api.onchange('bank_id')
    def domain_bank(self):
        domain = {}
        if self.bank_id:
            self.plafond_bank_id = None
            self.jenis_id = None
            self.no_rekening = None
            bank = self.env['wika.loan.plafond.detail'].search([
                ('plafond_id.bank_id', '=', self.bank_id.id)])
            domain = {'domain':{'no_rekening':[('bank_id','=',self.bank_id.id),
                ('currency_id','=',self.currency_id.id)],
                'jenis_id' :[('id','in',[x.jenis_id.id for x in bank]),('tipe','=','Cash')]},}
        return domain
    
    @api.onchange('jenis_id','bank_id')
    def domain_all(self):
        today = fields.Date.context_today(self)
        domain ={}
        if self.jenis_id and self.bank_id:
            plafond = self.env['wika.loan.plafond.detail'].search([
                ('plafond_id.bank_id', '=', self.bank_id.id),
                ('jenis_id', '=', self.jenis_id.id),
                ('sisa', '>', 0.0)])

            plafond_id = [x.id for x in plafond]
            domain = {'domain':{'plafond_bank_id':[('id','in',plafond_id)]}}
        return domain

    @api.depends('currency_id', 'nilai_pengajuan_asing')
    def auto_kurs(self):
        for record in self:
            if record.currency_id.name != 'IDR':
                record.kurs = record.currency_id.rate
            else:
                record.kurs = 1.0
            record.nilai_pengajuan = record.nilai_pengajuan_asing * record.kurs

    @api.onchange('currency_id','nilai_pengajuan_asing')
    def onchange_kurs(self):
        for record in self:
            record.currency_id.rate = 0.0
            if record.currency_id.name != 'IDR':
                record.kurs = record.currency_id.inverse_rate
            record.nilai_pengajuan = record.nilai_pengajuan_asing * record.kurs

    @api.onchange('nilai_pengajuan_asing', 'currency_id', 'kurs')
    @api.depends('nilai_pengajuan_asing', 'currency_id', 'kurs')
    def _hitung_kurs(self):
        if self.currency_id.name != 'IDR':
            if self.nilai_pengajuan_asing and self.kurs:
                self.nilai_pengajuan = (self.nilai_pengajuan_asing * self.kurs)

    # @api.onchange('bank_id')
    # def _onchange_bank(self):
    #     domain = {}
    #     usr = self.env['res.users'].search([('id', '=', self._uid)])
    #     for x in usr:
    #         if x.mcs_user_field:
    #             domain = {
    #                 'bank_id': [('id', 'in', [b.id for b in x.mcs_user_field])],
    #             }

    #     return {'domain': domain}

    @api.depends('nilai_pengajuan','stage_name')
    def _compute_sisa(self):
        for x in self:
            if x.stage_name == 'Cancel':
                x.sisa_pengajuan = 0.0
            else:
                nilai=0
                nclp = self.env['wika.cl.payment'].search([('cash_loan_id','=',x.id)])
                for z in nclp:
                    nilai=nilai+z.jumlah_bayar
                x.sisa_pengajuan=x.nilai_pengajuan-nilai

    @api.onchange('plafond_bank_id')
    def warning_plafond(self):
        if self.plafond_bank_id and self.plafond_bank_id.sisa <= 0.0:
            return {
                'warning': {'title': _('Warning!'), 
                    'message': _('Sisa Plafond anda "%s".\n Apakah akan dilanjutkan?')%self.plafond_bank_id.sisa}
                }      

    def perpanjangan(self):
        stage_sekarang = self.stage_id.sequence
        stage_next = self.env['wika.loan.stage'].search([('sequence','=',stage_sekarang+1),
            ('tipe','=','Cash'),
            ('name','=','Perpanjangan')])
        if stage_next.id:
            if self.pembayaran_ids:
                for pay in self.pembayaran_ids:
                    if pay.state == 'Belum Dibayar':            
                        pay.state= 'Perpanjangan'
                self.stage_id = stage_next.id
            else:
                raise ValidationError('Rencana Pembayaran tidak boleh kosong!')   

class WikaLoanLogPerpanjangan(models.Model):
    _name = 'wika.loan.log.perpanjangan'

    ke = fields.Integer(string='Ke')
    pembayaran_id = fields.Many2one(comodel_name='wika.cl.payment', string="CL Pembayaran", ondelete='cascade')
    loan_id = fields.Many2one(related='pembayaran_id.cash_loan_id', store=True)
    bunga_lama = fields.Float(string="Rate Bunga Lama")
    nilai_pokok_lama = fields.Float(string="Nilai Pokok Lama")
    nilai_bunga_lama = fields.Float(string="Nilai Bunga Lama")
    nilai_pokok_lama_asing= fields.Float(string="Nilai Pokok Asing Lama")
    nilai_bunga_lama_asing = fields.Float(string="Nilai Bunga Bunga Lama")
    tgl_eksekusi = fields.Date(string='Tanggal Pepranjangan')
    tgl_jatuh_tempo_lama = fields.Date(string='Tanggal Jatuh Tempo')


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
    total = fields.Float(string='Total', store=True, compute='_compute_total')
    nilai_pengajuan = fields.Float(related='cash_loan_id.nilai_pengajuan', string="Nilai Pengajuan")
    plafond_bank_id = fields.Many2one(related='cash_loan_id.plafond_bank_id', string="Plafond Bank", store=True)
    bank_id = fields.Many2one(related='cash_loan_id.bank_id', string="Bank", store=True)
    Csisa = fields.Float(string="Total (Dalam Juta)", store=True)
    rate_bunga_new = fields.Float(string='Rate Bunga Baru')
    nilai_bunga_new = fields.Float(string='Pembayaran Bunga Baru')
    nilai_bunga_asing_new = fields.Float(string='Pembayaran Bunga Asing Baru')


    # company_currency    = fields.Many2one(related='loan_id.company_currency',
    #                      string='Currency',store=True
    #                      )
    # currency_new        = fields.Many2one(comodel_name='res.currency',
    #                      string='New Currency'
    #                      )
    # kurs_awal           = fields.Float(related='loan_id.kurs',string='Kurs Pembukaan')    
    tgl_jatuh_tempo_new = fields.Date(string='Tanggal Jatuh Tempo')

    tgl_bayar = fields.Date(string='Tanggal Bayar',default=datetime.today())
    selisih_bayar = fields.Float(compute='_compute_selisih', readonly=True)
   
    
    tipe_bayar = fields.Boolean(string='Apakah sisanya akan di perpanjang?',default=False)

    # # Baru
    plaf_id = fields.Many2one('wika.plafond.bank', string="Plafond Bank")

    # plaf_id     = fields.Many2one(related='plafond_bank_id.plafond_id',store=True)
    Gsisa       = fields.Float(related='Csisa', store=True)
    perpanjangan_ids = fields.One2many(comodel_name='wika.loan.log.perpanjangan', string="History Perpanjangan",
        inverse_name='pembayaran_id', ondelete='cascade', index="true", copy=False)

    @api.depends('loan_id.plafond_bank_id.terpakai')
    def lunas(self):
        stage_next = self.env['wika.loan.stage'].search([
            ('name', '=', 'Lunas'),
            ('tipe', '=', 'Cash')], limit=1)
        today = fields.Date.context_today(self)
        for x in self:
            if x.nilai_pokok:               
                x.plafond_bank_id.terpakai = x.plafond_bank_id.terpakai - x.nilai_pokok                
            x.plafond_bank_id.sisa = x.plafond_bank_id.nilai - x.plafond_bank_id.terpakai
            x.plafond_bank_id.plafond_id.terpakai = sum(x.terpakai for x in self.plafond_bank_id.plafond_id.plafond_ids)                                 
            x.plafond_bank_id.plafond_id.sisa = x.plafond_bank_id.plafond_id.jumlah - x.plafond_bank_id.plafond_id.terpakai        
        self.loan_id.stage_id=stage_next.id
        self.state      = 'Lunas'
        self.jumlah_bayar = self.nilai_pokok
        self.tgl_bayar  = today

    # def action_proses(self):
    #     self.ensure_one()
    #     action = {
    #         'name': 'CL Pembayaran',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'wika.cl.payment',
    #         'view_mode': 'tree,form',
    #         'limit': 20,
    #         'views': [
    #             (self.env.ref('wika_cash_loan.wika_cl_payment_view_tree').id, 'tree'),
    #             (self.env.ref('wika_cash_loan.wika_cl_payment_view_form1').id, 'form')
    #         ],
    #         'context': self.env.context,
    #         'target': 'current',  # Tambahkan target jika diperlukan
    #     }
    #     return action

    def perpanjangan(self):
        if self.state == 'Belum Dibayar':
            self.state = 'Perpanjangan'
        log_perpanjangan = self.env['wika.loan.log.perpanjangan'].search([
            ('pembayaran_id', '=', self.id)])
        ke = 1
        if log_perpanjangan:
            for x in log_perpanjangan:
                ke += 1
        today = fields.Date.context_today(self)
        self.env['wika.loan.log.perpanjangan'].create({
            'loan_id': self.cash_loan_id.id,
            'ke': ke,
            'pembayaran_id': self.id,
            'bunga_lama': self.rate_bunga,
            'nilai_bunga_lama': self.nilai_bunga,
            'nilai_bunga_lama_asing': self.nilai_bunga_asing,
            'nilai_pokok_lama': self.nilai_pokok,
            'nilai_pokok_lama_asing': self.nilai_pokok_asing,
            'tgl_jatuh_tempo_lama': self.tgl_jatuh_tempo,
            'tgl_eksekusi': today})


        self.cash_loan_id.tgl_mulai = self.tgl_jatuh_tempo
        self.cash_loan_id.tgl_akhir = self.tgl_jatuh_tempo_new
        self.nilai_bunga = self.nilai_bunga_new
        self.nilai_bunga_asing = self.nilai_bunga_asing_new
        self.rate_bunga = self.rate_bunga_new
        self.tgl_jatuh_tempo = self.tgl_jatuh_tempo_new

    @api.depends('plafond_bank_id.terpakai')
    def bayar(self):
        stage_next = self.env['wika.loan.stage'].search([('name', '=', 'Lunas'),
            ('tipe', '=', 'Cash')],limit=1)
        stage_next2 = self.env['wika.loan.stage'].search([('name', '=', 'Perpanjangan'),
            ('tipe', '=', 'Cash')],limit=1)
        cr  = self.env['wika.cl.payment']
        today = fields.Date.context_today(self)
        if self.jumlah_bayar:
            if self.selisih_bayar > 0.0 and self.tipe_bayar == True :
                pembayaran = cr.create({                  
                    'cash_loan_id': self.cash_loan_id.id,
                    'nilai_pokok': self.selisih_bayar,
                    'nilai_bunga': self.nilai_bunga_new,
                    'jumlah_bayar': 0,
                    'plafond_bank_id': self.plafond_bank_id.id,
                    'bank_id': self.bank_id.id,
                    'tgl_jatuh_tempo': self.tgl_jatuh_tempo_new,
                    'currency_id': self.currency_new.id,
                    'keterangan' : 'Rollover',
                    'state': 'Perpanjangan'
                })
                self.cash_loan_id.stage_id = stage_next2.id
                self.cash_loan_id.stage_name = 'Perpanjangan'
                self.cash_loan_id.tgl_akhir = self.tgl_jatuh_tempo_new
            else:
                self.cash_loan_id.stage_id = stage_next.id
                self.cash_loan_id.stage_name = 'Lunas'
                self.cash_loan_id.tgl_akhir = self.tgl_jatuh_tempo

            self.plafond_bank_id.terpakai = self.plafond_bank_id.terpakai - self.jumlah_bayar 
            self.plafond_bank_id.plafond_id.terpakai = sum(x.terpakai for x in self.plafond_bank_id.plafond_id.plafond_ids)                                
            self.plafond_bank_id.sisa = self.plafond_bank_id.nilai - self.plafond_bank_id.terpakai
            self.plafond_bank_id.plafond_id.sisa = self.plafond_bank_id.plafond_id.jumlah - self.plafond_bank_id.plafond_id.terpakai
            self.tgl_bayar = today
            self.state = 'Lunas'

    @api.depends('nilai_pokok', 'nilai_bunga')
    def _compute_total(self):
        for x in self:
            x.total = (x.nilai_pokok + x.nilai_bunga)

    def action_perpanjangan(self):
        form_id = self.env.ref('wika_cash_loan.cl_pembayaran_form_view_perpanjangan')
        return {
            'name': 'TR',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wika.cl.payment',
            'view_id': form_id.id,
            'type': 'ir.actions.act_window',
            'res_id':self.id,
            'target': 'new',
            'context': {'default_id': self.id}
        }

    def action_bayar_view(self):
        form_id = self.env.ref('wika_cash_loan.wika_cl_payment_view_form2')
        return {
            'name': 'Form Pembayaran',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wika.cl.payment',
            'view_id': form_id.id,
            'type': 'ir.actions.act_window',
            'res_id':self.id,     
            'context': {'default_id': self.id,'default_jumlah_bayar': self.nilai_pokok},
            'target': 'new',
        }

    @api.depends('nilai_pokok', 'jumlah_bayar')
    def _compute_selisih(self):
        for x in self:
            if x.jumlah_bayar:
                x.selisih_bayar = x.nilai_pokok - x.jumlah_bayar
    
    @api.depends('total')
    def _compute_sisa(self):
        for rec in self:
            rec.Csisa=rec.total/1000000

    @api.depends('rate_bunga_new','nilai_pokok_asing','nilai_pokok')
    @api.onchange('rate_bunga_new')
    def onchange_nilai_bunga_asing_new(self):
        for x in self:
            if x.rate_bunga_new:
                x.nilai_bunga_asing_new = ((x.nilai_pokok_asing  * x.tenor) / 12)* x.rate_bunga_new
                x.nilai_bunga_new = ((x.nilai_pokok * x.tenor) / 12)* x.rate_bunga_new

    @api.onchange('jumlah_bayar')
    def _onchange_selisih(self):
        if self.jumlah_bayar and self.selisih_bayar > 0.0 :
            self.tipe_bayar = True
        elif self.jumlah_bayar and self.selisih_bayar == 0.0 :
            self.tipe_bayar = None
    
    @api.depends('nilai_pokok','loan_id.rate_bunga')
    @api.onchange('nilai_pokok')
    def onchange_nilai_bunga(self):
        for x in self:
            if x.nilai_pokok:
                x.jumlah_bayar = x.nilai_pokok
                x.nilai_bunga = ((x.nilai_pokok * x.tenor) / 12) * x.rate_bunga

    @api.depends('nilai_pokok_asing','rate_bunga','kurs_awal')
    @api.onchange('nilai_pokok_asing')
    def onchange_nilai_bunga_asing(self):
        for x in self:
            if x.nilai_pokok_asing:
                x.nilai_bunga_asing = ((x.nilai_pokok_asing  * x.tenor) / 12)* x.rate_bunga
                x.nilai_pokok = (x.nilai_pokok_asing * x.kurs_awal)
                x.nilai_bunga = ((x.nilai_pokok  * x.tenor) / 12)* x.rate_bunga

    @api.onchange('rate_bunga_new')
    def onchange_nilai_bunga_baru(self):
        for x in self:
            if x.state=='Perpanjangan' and x.rate_bunga_new and x.selisih_bayar > 0.0 :
                x.nilai_bunga_new = ((x.selisih_bayar  * x.tenor) / 12)* x.rate_bunga_new

    @api.depends('nilai_pokok', 'nilai_bunga')
    def _compute_total(self):
        for x in self:
            x.total = (x.nilai_pokok + x.nilai_bunga)