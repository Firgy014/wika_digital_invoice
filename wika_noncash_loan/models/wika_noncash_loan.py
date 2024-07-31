from odoo import api, fields, models, _
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError, Warning, AccessError


class WikaNonCashLoan(models.Model):
    _name = 'wika.noncash.loan'
    _description = 'Non Cash Loan'
    _inherit = 'mail.thread'
    _order = 'sisa_outstanding desc'

    plaf_id = fields.Many2one(
        comodel_name='wika.plafond.bank', 
        string="Plafond ID", 
        related='plafond_bank_id.plafond_id', 
        store=True
    )
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
    department_id = fields.Many2one(comodel_name='res.branch', index=True, string='Divisi')
    jumlah_pengajuan = fields.Float(string='Nilai Pengajuan', index=True)
    jumlah_pengajuan_asing = fields.Float(string='Nilai Pengajuan Asing', copy=False)
    dalam_proses = fields.Float(string='Dalam Proses', default=0, copy=False)
    sisa_outstanding = fields.Float(string='Outstanding', default=0, copy=False)
    stage_id = fields.Many2one(comodel_name='wika.loan.stage', domain=[('tipe','=','Non Cash'),],
        string='Status', copy=False, track_visibility='onchange', index=True)
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency')
    stage_name = fields.Char(related='stage_id.name', string='Status Name', store=True, index=True)
    bank_id = fields.Many2one(comodel_name='res.bank', string="Bank", index=True)
    jenis_id = fields.Many2one(comodel_name='wika.loan.jenis',
        string="Kriteria")
    project_id = fields.Many2one(comodel_name='project.project', string="Proyek")
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
    tgl_akhir_perkiraan = fields.Date(string='Tanggal Akhir Perkiraan')
    # tgl_akseptasi   = fields.Date(string='Tanggal Akseptasi')
    rate_bunga      = fields.Float(string='Rate Bunga (%)')
    # total_bunga     = fields.Float(
    #                         compute='_cal_amount_all',
    #                         string='Nominal Bunga',
    #                         store=True
    #                         )
    #                      )
    stage_id1       = fields.Many2one(related='stage_id',store=False)
    stage_id2       = fields.Many2one(related='stage_id',store=False)
    

    tipe_jenis = fields.Many2one(string='Tipe Kriteria', comodel_name='wika.tipe.jenis')                    
    tipe_jenis_name = fields.Char(related='tipe_jenis.name', string="Tipe jenis Name")
    catatan = fields.Text(string='Catatan') 
    tgl_swift                   = fields.Date(string='Tanggal Swift',copy=False)
    payment_ids                 = fields.One2many(comodel_name='wika.ncl.pembayaran', string="Rencana Pembayaran",
                                  inverse_name='loan_id', ondelete='cascade', index="true",copy=False)
    # payment_ids2                 = fields.One2many(comodel_name='ncl.pembayaran', string="Rencana Pembayaran",
    #                               inverse_name='loan_id', ondelete='cascade', index="true",copy=False)
    # payment_ids3 = fields.One2many(comodel_name='ncl.pembayaran', string="Rencana Pembayaran",
    #                                inverse_name='loan_id', ondelete='cascade', index="true", copy=False)
    # payment_ids4 = fields.One2many(comodel_name='ncl.pembayaran', string="Rencana Pembayaran",
    #                                inverse_name='loan_id', ondelete='cascade', index="true", copy=False)
    payment_id                  = fields.Many2one('wika.ncl.pembayaran',string='Pembayaran',copy=False)
    # total_pokok                 = fields.Float(string='Total Pokok', compute='_compute_total',copy=False)
    # total_bunga                 = fields.Float(string='Total Bunga', compute='_compute_total',copy=False)
    anak_perusahaan = fields.Boolean(related='branch_id.anak_perusahaan',store=False)
    department_parent = fields.Many2one(related='branch_id.parent_id',store=False)
    nama_vendor = fields.Char(string='Nama Vendor/Owner')
    nama_nasabah = fields.Char(string='Nama Nasabah') 
    masa_klaim = fields.Integer(string='Masa Klaim (Hari)')
    tgl_jatuh_tempo = fields.Date(string='Tanggal Jatuh Tempo')
    payment_keterangan          = fields.Char(related='payment_id.keterangan',string='Keterangan Bayar',copy=False)
    tgl_bayar                   = fields.Date(related='payment_id.tgl_bayar',string='Tanggal Bayar',copy=False)
    kurs                        = fields.Float(string='Kurs')                    
    nomor_surat = fields.Char(string='Nomor Surat')
    tenor = fields.Integer(string='Tenor Hari')
    sejak = fields.Char(string='Terhitung Sejak') 
    sisa_plafond = fields.Float(related='plafond_bank_id.plafond_id.sisa', string='Sisa Plafond')
    sisa_plafond_max = fields.Float(related='plafond_bank_id.sisa', string='Sisa Plafond Max')
    # plaf_id                     = fields.Many2one(related='plafond_bank_id.plafond_id',store=True)
    company_currency = fields.Many2one(string='Currency', comodel_name="res.currency")

    status_loan = fields.Selection(string="Status Aktif Loan", selection=[
        ('Aktif', 'Aktif'),
        ('Tidak Aktif', 'Tidak Aktif')], default='Aktif',copy=False)
    keterangan_hari_mulai       = fields.Char(string="Keterangan Hari Mulai", store=True)
    keterangan_hari_akhir       = fields.Char(string="Keterangan Hari Akhir", store=True)

    # amandemen_ids               = fields.One2many(comodel_name='loan.amandemen', string="History Amandemen",
    #                               inverse_name='loan_id', ondelete='cascade', index="true",copy=False)
    # amandemen_ke                = fields.Integer(string='Amandemen Ke', default=0,copy=False)
    # jumlah_pengajuan_baru       = fields.Float(string='Nilai Pengajuan')
    # jumlah_pengajuan_asing_baru = fields.Float(string='Nilai Pengajuan Asing')
    # kurs_baru                   = fields.Float(string='Kurs')
    # tgl_mulai_baru              = fields.Date(string='Tanggal Mulai')
    # tgl_akhir_baru              = fields.Date(string='Tanggal Akhir')
    # comp_amandemen              = fields.Integer(string='Amandemen Ke', compute='_compute_amandemen',copy=False)
    tgl_jatuh_tempo_baru = fields.Date(string='Tanggal Jatuh Tempo')
    # keterangan_hari_mulai_baru       = fields.Char(string="Keterangan Hari Mulai", store=True)
    # keterangan_hari_akhir_baru       = fields.Char(string="Keterangan Hari Akhir", store=True)
    catatan_sistem                   = fields.Text(string="Catatan Sistem")

    jenis_nasabah = fields.Selection([
        ('SUPPLIER', 'Supplier'),
        ('SUBKONT', 'Subkon')
    ], string='Jenis Nasabah')
    nomor_bukti = fields.Char('Nomor Bukti')
    nomor_kontrak = fields.Char('Nomor Kontrak')
    nama_barang = fields.Char('Nama Barang')
    tanggal_kontrak = fields.Date('Tanggal Kontrak')
    nilai_pokok_tagihan = fields.Float('Nilai Pokok Tagihan')
    ppn = fields.Float('PPN')
    nilai_pokok_ppn = fields.Float('Nilai Pokok + PPN')
    potongan_pph_persen = fields.Float('Potongan PPH (%)')
    potongan_pph = fields.Float('Potongan PPH (Rp)')
    potongan_lain = fields.Float('Potongan Lain')
    nilai_tagihan_netto = fields.Float('Nilai Tagihan Netto')
    nilai_progress = fields.Float('Nilai Progress')
    potongan_um = fields.Float('Potongan Uang Muka')
    is_pmcs = fields.Boolean(string="Dari PMCS", default=False)
    step_approve       = fields.Integer(string='Step Approve',default=1,copy=False)
    history_approval_ids = fields.One2many('wika.noncash.loan.approval.line', 'ncl_id', string='List Approval')
    # default_debit_acc = fields.Many2one(comodel_name='account.account', string="Default Debit Account",
    #                                     domain="[('user_type_id','=',1)]")
    # default_credit_acc = fields.Many2one(comodel_name='account.account', string="Default Credit Account",
    #                                      domain="[('user_type_id','=',2)]")

    invoice_id = fields.Many2one(string="Invoice", comodel_name='account.move')
    # move_id = fields.Many2one(string="Journal Entry", comodel_name='account.move')
    # active = fields.Boolean('Active',
    #                         help="If the active field is set to False, it will allow you to hide the account without removing it.",
    #                         default=True)
    keterangan_html = fields.Html(compute='_compute_keterangan_html')
    # @api.model
    # def create(self, vals):
    #     res = super(WikaNonCashLoan, self).create(vals)
    #     res.name= self.env['ir.sequence'].next_by_code('wika.berita.acara.pembayaran')
    #     res.assign_todo_first()
    #     res._compute_cut_over()
    #     return res
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)
    level = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat')
    ], string='Level',compute='_compute_level')
    nomor_memorial = fields.Char('Nomor Memorial')
    nilai_akutansi      = fields.Float(string='Nilai Akutansi')
    no_sap = fields.Char('No Doc SAP')
    payment_proposal_id_sap              = fields.Char(string='Payment Proposal Id SAP')
    line_item_sap = fields.Char(string='Line Item SAP')
    fiscal_year_sap = fields.Char(string='Fiscal Year SAP')
    run_date_sap= fields.Date(string='Run Date SAP',copy=False)
    from_sap            = fields.Boolean(string='From SAP',default=False,copy=False)
    upload_to_sap       = fields.Boolean(string='Upload to SAP',default=False)
    send= fields.Boolean(string='Send to SAP',default=False,copy=False)
    identifier          = fields.Char(string='Identifier',copy=False)
    is_pmcs = fields.Boolean(string="Dari PMCS", default=False)
    allocation_id = fields.Many2one('wika.loan.allocation', string='Allocation')
    kelompok            = fields.Selection([
        ('Revolving Loans','Revolving Loans'),
        ('Terms Loan','Terms Loan')],string='Kelompok', 
    related='jenis_id.kelompok',store=True)

    @api.onchange('nilai_progress', 'potongan_um')
    def _nilai_pokok_tagihan(self):
        for x in self:
            if not x.is_pmcs:
                x.nilai_pokok_tagihan = x.nilai_progress + x.potongan_um

    @api.onchange('nilai_pokok_tagihan')
    def _nilai_ppn(self):
        for x in self:
            if not x.is_pmcs:
                x.ppn = round((x.nilai_pokok_tagihan/10))

    @api.onchange('nilai_pokok_tagihan','potongan_pph_persen')
    def _nilai_pph_persen(self):
        for x in self:
            if not x.is_pmcs:
                x.potongan_pph = round((x.nilai_pokok_tagihan * x.potongan_pph_persen)/100)

    @api.onchange('nilai_pokok_tagihan', 'ppn')
    def _nilai_pokok_ppn(self):
        for x in self:
            if not x.is_pmcs:
                x.nilai_pokok_ppn = x.nilai_pokok_tagihan + x.ppn

    @api.onchange('nilai_pokok_ppn', 'potongan_pph', 'potongan_lain')
    def _nilai_tagihan(self):
        for x in self:
            if not x.is_pmcs:
                x.nilai_tagihan_netto = x.nilai_pokok_ppn - x.potongan_pph - x.potongan_lain

    @api.onchange('nilai_pokok_tagihan', 'potongan_pph','potongan_lain')
    def _nilai_pengajuan(self):
        for x in self:
            if not x.is_pmcs:
                jumlah_pengajuan = x.nilai_pokok_tagihan - x.potongan_pph - x.potongan_lain
                x.jumlah_pengajuan = int(jumlah_pengajuan)

    # @api.onchange('jenis_id')
    # def onchange_jenis(self):
    #     self.nama_jenis = self.jenis_id.jenis
    #     self.plafond_bank_id = None

    @api.constrains('masa_klaim','jumlah_pengajuan','jumlah_pengajuan_asing')
    def _check_masaklaim(self):
        if self.masa_klaim < 0:
            raise ValidationError('Masa Klaim harus bernilai positif!')
        elif self.jumlah_pengajuan <= 0:
            raise ValidationError('Nilai Pengajuan harus lebih dari 0')
        elif self.jumlah_pengajuan <= 0 and self.currency_id != 13:
            raise ValidationError('Nilai Pengajuan Asing harus lebih dari 0')

    @api.onchange('jenis_id')
    def onchange_jenis(self):
        self.nama_jenis=self.jenis_id.nama
    
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
            
    @api.model
    def create(self, vals):
        res = super(WikaNonCashLoan, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            res.name = self.env['ir.sequence'].next_by_code('wika.noncash.loan') or  _('New')
            res.assign_todo_first()
        return res

    def assign_todo_first(self):
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'wika.noncash.loan')], limit=1)

        for res in self:
            level = res.level
            first_user = False

            if level:
                approval_id = self.env['wika.approval.setting'].sudo().search(
                    [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
                
                if not approval_id:
                    _logger.warning("Approval setting not found for level %s", level)
                    continue

                approval_line_id = self.env['wika.approval.setting.line'].search([
                    ('sequence', '=', 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)

                if not approval_line_id:
                    _logger.warning("Approval line not found for approval_id %s", approval_id.id)
                    continue

                groups_id = approval_line_id.groups_id

                if groups_id:
                    for x in groups_id.users:
                        if level == 'Proyek' and res.project_id in x.project_ids:
                            first_user = x.id
                        elif level == 'Divisi Operasi' and x.branch_id == res.branch_id:
                            first_user = x.id
                        elif level == 'Divisi Fungsi' and x.department_id == res.department_id:
                            first_user = x.id

                _logger.info("First user assigned: %s", first_user)

                # Create todo activity
                if first_user:
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': 4,  # Ensure this ID corresponds to the correct activity type
                        'res_model_id': model_id.id,
                        'res_id': res.id,
                        'user_id': first_user,
                        'date_deadline': fields.Date.today() + timedelta(days=2),
                        'state': 'planned',
                        'summary': f"Need to ask for approval {model_id.name}!"
                    })
                else:
                    _logger.warning("No valid user found for activity assignment.")

    def action_input(self):
        stage_default = self.env['wika.loan.stage'].search([
            ('tipe', '=', 'Non Cash'),
            ('name', '=', 'Pengajuan'),
            ('request', '=', True)
        ], limit=1)
        _logger.info('CHECKK DEFAULT STAGE Action Input - Default Stage ID: %s', stage_default.id)
        action = {
            'name': 'NCL Input',
            'type': 'ir.actions.act_window',
            'res_model': 'wika.noncash.loan',
            'view_mode': 'tree,form',
            'view_type': "form",
            'view_id': False,
            'views': [
                (self.env.ref('wika_noncash_loan.wika_ncl_input_view_tree').id, 'tree'),
                (self.env.ref('wika_noncash_loan.wika_ncl_input_view_form').id, 'form')
            ],
            'context': {'default_stage_id': stage_default.id},
            'domain': [('stage_id.name', 'in', ['Pengajuan', 'Proses Approval', 'Approve', 'Reject'])]
        }
        return action

    def submit(self):
        if self.jenis_id.lock_date and self.tgl_pembukaan:
            today = datetime.today().strftime('%Y-%m-')
            end_date3 = self.tgl_pembukaan.strftime('%Y-%m-')
            if end_date3 != today:
                raise ValidationError('Periksa Kembali Tanggal Pembukaan anda!')

        if self.nama_jenis in ['SCF', 'SKBDN/LC']:
            jenis = self.env['wika.loan.jenis'].search([('nama', '=', self.nama_jenis), ('tipe', '=', 'Non Cash')], limit=1)
            tgl_formatted = self.tgl_pembukaan
            tgl_mulai = "%s-01-01" % tgl_formatted.year
            tgl_akhir = "%s-12-31" % tgl_formatted.year
            prognos = self.env['wika.loan.prognosa'].search([
                ('bank_id', '=', self.bank_id.id),
                ('tipe_id', '=', jenis.id),
                ('branch_id', '=', self.branch_id.id),
                ('tgl_mulai', '>=', tgl_mulai),
                ('tgl_akhir', '<=', tgl_akhir),
            ], limit=1)
            progline = self.env['wika.loan.prognosa.line'].search([
                ('prognosa_id', '=', prognos.id),
                ('bulan', '=', tgl_formatted.month)
            ], limit=1)
            if not progline:
                raise ValidationError("Tidak ada prognosa di bulan pembukaan yang diisi!")
            else:
                sisa = progline.nilai_pembukaan - progline.terpakai
                if sisa < self.jumlah_pengajuan:
                    raise ValidationError("Prognosa di bulan pembukaan yang diisi tidak mencukupi!")

        cek = False
        level = self.level
        model_id = self.env['ir.model'].search([('model', '=', 'wika.noncash.loan')], limit=1)
        if level:
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
            _logger.info('CHECK APPROVAL ID: %s', approval_id.id)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu NCL  tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', 1),
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

        if cek:
            if self.activity_ids:
                for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                    if x.user_id.id == self._uid:
                        x.status = 'approved'
                        x.action_done()
                stage_sekarang = self.stage_id.sequence
                stage_next = self.env['wika.loan.stage'].search([('sequence', '=', stage_sekarang + 1),
                    ('tipe', '=', 'Non Cash'),
                    ('name', '=', 'Proses Approval')], limit=1)
                if stage_next:
                    self.stage_id = stage_next.id
                else:
                    raise ValidationError('Tahap berikutnya tidak ditemukan!')

                self.step_approve += 1

                # Create history approval
                self.env['wika.noncash.loan.approval.line'].sudo().create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Submit NCL',
                    'ncl_id': self.id
                })

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
                                    [('model', '=', 'wika.noncash.loan')], limit=1).id,
                                'res_id': self.id,
                                'user_id': first_user,
                                'date_deadline': fields.Date.today() + timedelta(days=2),
                                'state': 'planned',
                                'status': 'to_approve',
                                'summary': """Need Approve"""
                            })
        else:
            raise ValidationError('User Akses Anda tidak berhak Submit!')

    def approve_input(self):
        if self.jenis_id.lock_date and self.tgl_pembukaan:
            today = datetime.today().strftime('%Y-%m-')
            end_date3 = self.tgl_pembukaan.strftime('%Y-%m-')
            if end_date3!=today:
                raise ValidationError('Periksa Kembali Tanggal Pembukaan anda!')

        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'wika.noncash.loan')], limit=1)
        level = self.level
        if level:
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu NCL tidak ditemukan. Silakan hubungi Administrator!')

            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            print(approval_line_id)
            groups_id = approval_line_id.groups_id
            if groups_id:
                print(groups_id.name)
                for x in groups_id.users:
                    if level == 'Proyek' and self.project_id in x.project_ids and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True

        if cek:
            # Proses approval
            self.env['wika.noncash.loan.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id.id,
                'date': datetime.now(),
                'note': 'Approved',
                'ncl_id': self.id
            })

            if approval_id.total_approve == self.step_approve:
                # Proses akhir persetujuan
                stage_next = self.env['wika.loan.stage'].search([
                    ('tipe', '=', 'Non Cash'),
                    ('name', '=', 'Pembukaan')
                ], limit=1)
                self.stage_id = stage_next.id
                self.step_approve = 1
            else:
                # Update stage dan step approval
                self.step_approve += 1
                stage_next = self.env['wika.loan.stage'].search([
                    ('sequence', '=', self.stage_id.sequence + 1),
                    ('tipe', '=', 'Non Cash'),
                    ('name', '=', 'Approve')
                ], limit=1)
                if stage_next:
                    self.stage_id = stage_next.id

                # Cari approval setting line berikutnya
                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level', '=', level),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                print("groups", groups_line_next)
                groups_id_next = groups_line_next.groups_id

                first_user = False
                if groups_id_next:
                    print(groups_id_next.name)
                    for x in groups_id_next.users:
                        if level == 'Proyek' and (x.branch_id == self.branch_id or x.branch_id.parent_id.code == 'Pusat'):
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                            first_user = x.id

                    if first_user:
                        # Buat aktivitas approval untuk user berikutnya
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': model_id.id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': "Need Approval NCL"
                        })
                    else:
                        raise ValidationError('User Role Next Approval Belum di Setting!')

                # Cek jika level_role adalah 'Proyek' dan user ini adalah user terakhir yang menyetujui
                if approval_line_id.level_role == 'Proyek':
                    # Ambil semua user 'Proyek' yang belum menyetujui
                    pending_users = self.env['wika.approval.setting.line'].search([
                        ('approval_id', '=', approval_id.id),
                        ('level_role', '=', 'Proyek'),
                        ('sequence', '>', self.step_approve)
                    ]).mapped('groups_id.users')
                    
                    # Jika tidak ada user 'Proyek' yang tersisa untuk menyetujui
                    if not any(user.id != self._uid for user in pending_users):
                        stage_next = self.env['wika.loan.stage'].search([
                            ('tipe', '=', 'Non Cash'),
                            ('name', '=', 'Pembukaan')
                        ], limit=1)
                        self.stage_id = stage_next.id

            # Update status aktivitas yang sudah ada
            if self.activity_ids:
                for activity in self.activity_ids.filtered(lambda a: a.status != 'approved'):
                    if activity.user_id.id == self._uid:
                        activity.status = 'approved'
                        activity.action_done()
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def request(self):
        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'wika.noncash.loan')], limit=1)
        
        # Langsung menetapkan level sebagai 'Pusat'
        level = 'Pusat'
        
        approval_id = self.env['wika.approval.setting'].sudo().search(
            [('model_id', '=', model_id.id)], limit=1)
        
        if not approval_id:
            raise ValidationError(
                'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')

        approval_line_id = self.env['wika.approval.setting.line'].search([
            ('sequence', '=', self.step_approve),
            ('approval_id', '=', approval_id.id),
            ('level_role', '=', level)
        ], limit=1)
        
        # if not approval_line_id:
        #     raise ValidationError('User Role Next Approval Belum di Setting!')
        
        groups_id = approval_line_id.groups_id
        
        if groups_id:
            for x in groups_id.users:
                if x.id == self._uid:
                    cek = True

        if cek:
            # Proses approval
            self.env['wika.noncash.loan.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id.id,
                'date': datetime.now(),
                'note': 'Approved',
                'ncl_id': self.id
            })

            stage_sekarang = self.stage_id.sequence
            # Proses akhir persetujuan
            stage_next = self.env['wika.loan.stage'].search([
                ('sequence', '=', stage_sekarang + 1),
                ('tipe', '=', 'Non Cash'),
                ('name', '=', 'Diajukan')
            ], limit=1)
            if stage_next:
                self.stage_id = stage_next.id
                self.step_approve += 1
            # else:
            #     # Update stage dan step approval
            #     self.step_approve += 1
            #     stage_next = self.env['wika.loan.stage'].search([
            #         ('sequence', '=', stage_sekarang + 1),
            #         ('tipe', '=', 'Non Cash'),
            #         ('name', '=', 'Diajukan')
            #     ], limit=1)
            #     if stage_next:
            #         self.stage_id = stage_next.id

                # Cari approval setting line berikutnya
                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level_role', '=', level),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                
                groups_id_next = groups_line_next.groups_id

                first_user = False
                if groups_id_next:
                    for x in groups_id_next.users:
                        first_user = x.id
                        break

                    if first_user:
                        # Buat aktivitas approval untuk user berikutnya
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': model_id.id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': "Need Approval NCL"
                        })
                    else:
                        raise ValidationError('User Role Next Approval Belum di Setting!')

            # Update status aktivitas yang sudah ada
            if self.activity_ids:
                for activity in self.activity_ids.filtered(lambda a: a.status != 'approved'):
                    if activity.user_id.id == self._uid:
                        activity.status = 'approved'
                        activity.action_done()
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def approve(self):
        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'wika.noncash.loan')], limit=1)
        plafond = self.env['wika.loan.plafond.detail'].search([('id', '=', self.plafond_bank_id.id)])
        
        # Langsung menetapkan level sebagai 'Pusat'
        level = 'Pusat'
        
        approval_id = self.env['wika.approval.setting'].sudo().search(
            [('model_id', '=', model_id.id)], limit=1)
        
        if not approval_id:
            raise ValidationError(
                'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')

        approval_line_id = self.env['wika.approval.setting.line'].search([
            ('sequence', '=', self.step_approve),
            ('approval_id', '=', approval_id.id),
            ('level_role', '=', level)
        ], limit=1)
        
        # if not approval_line_id:
        #     raise ValidationError('User Role Next Approval Belum di Setting!')
        
        groups_id = approval_line_id.groups_id
        
        if groups_id:
            for x in groups_id.users:
                if x.id == self._uid:
                    cek = True

        if cek:
            # Proses approval
            self.env['wika.noncash.loan.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id.id,
                'date': datetime.now(),
                'note': 'Approved',
                'ncl_id': self.id
            })
            if self.status_loan == 'Aktif':
                for data in plafond:
                    use = sum(x.jumlah_pengajuan for x in self)
                    plafond.terpakai += float(use)
                    plafond.pengajuan -= float(use)
                    plafond.plafond_id.terpakai += float(use)
                    plafond.sisa = plafond.nilai - plafond.nilai_book - plafond.terpakai
                    plafond.plafond_id.sisa = plafond.plafond_id.jumlah - plafond.plafond_id.terpakai - plafond.plafond_id.nilai_book
                
                self.tgl_akhir = self.tgl_akhir_perkiraan
                
                stage_next = self.env['wika.loan.stage'].search([
                    ('tipe', '=', 'Non Cash'),
                    ('name', '=', 'Disetujui')
                ], limit=1)

                if stage_next:
                    self.stage_id = stage_next.id
                else:
                    raise ValidationError("Tahap 'Disetujui' tidak ditemukan!")

            self.step_approve += 1

            if self.step_approve < approval_id.total_approve:
                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level_role', '=', level),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                
            groups_id_next = groups_line_next.groups_id

            first_user = False
            if groups_id_next:
                for x in groups_id_next.users:
                    first_user = x.id
                    break

                if first_user:
                    # Buat aktivitas approval untuk user berikutnya
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': 4,
                        'res_model_id': model_id.id,
                        'res_id': self.id,
                        'user_id': first_user,
                        'date_deadline': fields.Date.today() + timedelta(days=2),
                        'state': 'planned',
                        'status': 'to_approve',
                        'summary': "Need Approval NCL"
                    })
                else:
                    raise ValidationError('User Role Next Approval Belum di Setting!')

            # Update status aktivitas yang sudah ada
            if self.activity_ids:
                for activity in self.activity_ids.filtered(lambda a: a.status != 'approved'):
                    if activity.user_id.id == self._uid:
                        activity.status = 'approved'
                        activity.action_done()
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def proses(self):
        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'wika.noncash.loan')], limit=1)
        
        # Langsung menetapkan level sebagai 'Pusat'
        level = 'Pusat'
        
        approval_id = self.env['wika.approval.setting'].sudo().search(
            [('model_id', '=', model_id.id)], limit=1)
        
        if not approval_id:
            raise ValidationError(
                'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')

        approval_line_id = self.env['wika.approval.setting.line'].search([
            ('sequence', '=', self.step_approve),
            ('approval_id', '=', approval_id.id),
            ('level_role', '=', level)
        ], limit=1)
        
        # if not approval_line_id:
        #     raise ValidationError('User Role Next Approval Belum di Setting!')
        
        groups_id = approval_line_id.groups_id
        
        if groups_id:
            for x in groups_id.users:
                if x.id == self._uid:
                    cek = True

        if cek:
            # Proses approval
            self.env['wika.noncash.loan.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id.id,
                'date': datetime.now(),
                'note': 'Approved',
                'ncl_id': self.id
            })

            stage_sekarang = self.stage_id.sequence
            # Proses akhir persetujuan
            stage_next = self.env['wika.loan.stage'].search([
                ('sequence','=',stage_sekarang+1),
                ('tipe','=','Non Cash'),
                ('name','=','PENERBITAN')
            ], limit=1)
            if stage_next:
                self.stage_id = stage_next.id
                self.step_approve += 1

                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level_role', '=', level),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                
                groups_id_next = groups_line_next.groups_id

                first_user = False
                if groups_id_next:
                    for x in groups_id_next.users:
                        first_user = x.id
                        break

                    if first_user:
                        # Buat aktivitas approval untuk user berikutnya
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': model_id.id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': "Need Approval NCL"
                        })
                    else:
                        raise ValidationError('User Role Next Approval Belum di Setting!')

            # Update status aktivitas yang sudah ada
            if self.activity_ids:
                for activity in self.activity_ids.filtered(lambda a: a.status != 'approved'):
                    if activity.user_id.id == self._uid:
                        activity.status = 'approved'
                        activity.action_done()
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def setuju(self):
        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'wika.noncash.loan')], limit=1)
        plafond = self.env['wika.loan.plafond.detail'].search([('id', '=', self.plafond_bank_id.id)])
        # Langsung menetapkan level sebagai 'Pusat'
        level = 'Pusat'
        
        approval_id = self.env['wika.approval.setting'].sudo().search(
            [('model_id', '=', model_id.id)], limit=1)
        
        if not approval_id:
            raise ValidationError(
                'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')

        approval_line_id = self.env['wika.approval.setting.line'].search([
            ('sequence', '=', self.step_approve),
            ('approval_id', '=', approval_id.id),
            ('level_role', '=', level)
        ], limit=1)
        
        # if not approval_line_id:
        #     raise ValidationError('User Role Next Approval Belum di Setting!')
        
        groups_id = approval_line_id.groups_id
        
        if groups_id:
            for x in groups_id.users:
                if x.id == self._uid:
                    cek = True

        if cek:
            # Proses approval
            self.env['wika.noncash.loan.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id.id,
                'date': datetime.now(),
                'note': 'Approved',
                'ncl_id': self.id
            })

            if self.nama_jenis == 'SCF':  
                
                scf_detail = {
                    'loan_id': self.id,
                    'no_swift_akseptasi':self.no_swift,
                    'tgl_swift_akseptasi': self.tgl_swift,
                    'tgl_jatuh_tempo': self.tgl_akhir,
                    'nilai_pokok': self.jumlah_pengajuan,
                }
                detail = self.env['wika.ncl.pembayaran'].create(scf_detail)
                # self.stage_id = stage_next.id
                self.upload_to_sap = True

                if self.status_loan=="Tidak Aktif":
                    for data in plafond:
                        use = self.jumlah_pengajuan
                        plafond.terpakai = plafond.terpakai + float(use)
                        plafond.plafond_id.terpakai = plafond.plafond_id.terpakai + float(use)
                        plafond.sisa = plafond.nilai - plafond.nilai_book - plafond.terpakai
                        plafond.plafond_id.sisa = plafond.plafond_id.jumlah - plafond.plafond_id.terpakai - plafond.plafond_id.nilai_book

            elif self.nama_jenis == 'BG':
                pembayaran = {                  
                    'loan_id': self.id,
                    'nama_jenis' :self.nama_jenis,
                    'plafond_bank_id' : self.plafond_bank_id.id,
                    'bank_id': self.bank_id.id,
                    'branch_id': self.branch_id.id,
                    'currency_id': self.currency_id.id,
                    'masa_klaim': self.masa_klaim,
                    'nilai_pokok': self.jumlah_pengajuan,
                    'nilai_pokok_asing': self.jumlah_pengajuan_asing,
                    'tgl_swift_akseptasi': self.tgl_swift,
                    'no_swift_akseptasi': self.no_swift,
                    'tgl_jatuh_tempo' : self.tgl_jatuh_tempo,
                    'state' : 'Belum Dibayar'
                    }
                detail = self.env['wika.ncl.pembayaran'].create(pembayaran)
                self.payment_id = detail.id
                self.stage_id = stage_next.id
                self.upload_to_sap = True
                if self.status_loan=="Tidak Aktif":
                    for data in plafond:
                        use = self.jumlah_pengajuan
                        plafond.terpakai = plafond.terpakai + float(use)
                        plafond.plafond_id.terpakai = plafond.plafond_id.terpakai + float(use)
                        plafond.sisa = plafond.nilai - plafond.nilai_book - plafond.terpakai
                        plafond.plafond_id.sisa = plafond.plafond_id.jumlah - plafond.plafond_id.terpakai - plafond.plafond_id.nilai_book
            else:
                self.stage_id = stage_next.id
                self.upload_to_sap = True

            stage_sekarang = self.stage_id.sequence
            # Proses akhir persetujuan
            stage_next = self.env['wika.loan.stage'].search([
                ('sequence','=',stage_sekarang+1),
                ('tipe','=','Non Cash'),
                ('name','=','Setuju')
                ], limit=1)
            if stage_next:
                self.stage_id = stage_next.id
                self.step_approve += 1

                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level_role', '=', level),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                
                groups_id_next = groups_line_next.groups_id

                first_user = False
                if groups_id_next:
                    for x in groups_id_next.users:
                        first_user = x.id
                        break

                    if first_user:
                        # Buat aktivitas approval untuk user berikutnya
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': model_id.id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': "Need Approval NCL"
                        })
                    else:
                        raise ValidationError('User Role Next Approval Belum di Setting!')

            # Update status aktivitas yang sudah ada
            if self.activity_ids:
                for activity in self.activity_ids.filtered(lambda a: a.status != 'approved'):
                    if activity.user_id.id == self._uid:
                        activity.status = 'approved'
                        activity.action_done()
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')
    
    def perpanjangan(self):
        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'wika.noncash.loan')], limit=1)
        
        # Langsung menetapkan level sebagai 'Pusat'
        level = 'Pusat'
        
        approval_id = self.env['wika.approval.setting'].sudo().search(
            [('model_id', '=', model_id.id)], limit=1)
        
        if not approval_id:
            raise ValidationError(
                'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')

        approval_line_id = self.env['wika.approval.setting.line'].search([
            ('sequence', '=', self.step_approve),
            ('approval_id', '=', approval_id.id),
            ('level_role', '=', level)
        ], limit=1)
        
        # if not approval_line_id:
        #     raise ValidationError('User Role Next Approval Belum di Setting!')
        
        groups_id = approval_line_id.groups_id
        
        if groups_id:
            for x in groups_id.users:
                if x.id == self._uid:
                    cek = True

        if cek:
            # Proses approval
            self.env['wika.noncash.loan.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id.id,
                'date': datetime.now(),
                'note': 'Approved',
                'ncl_id': self.id
            })

            stage_sekarang = self.stage_id.sequence
            # Proses akhir persetujuan
            stage_next = self.env['wika.loan.stage'].search([
                ('tipe','=','Non Cash'),
                ('name','=','Perpanjangan')
            ], limit=1)
            if stage_next:
                self.stage_id = stage_next.id
                self.step_approve += 1

                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level_role', '=', level),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                
                groups_id_next = groups_line_next.groups_id

                first_user = False
                if groups_id_next:
                    for x in groups_id_next.users:
                        first_user = x.id
                        break

                    if first_user:
                        # Buat aktivitas approval untuk user berikutnya
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': model_id.id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': "Need Approval NCL"
                        })
                    else:
                        raise ValidationError('User Role Next Approval Belum di Setting!')

            # Update status aktivitas yang sudah ada
            if self.activity_ids:
                for activity in self.activity_ids.filtered(lambda a: a.status != 'approved'):
                    if activity.user_id.id == self._uid:
                        activity.status = 'approved'
                        activity.action_done()
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def dok_diterima(self):
        stage_sekarang = self.stage_id.sequence
        stage_next = self.env['wika.loan.stage'].search([
            ('sequence','=',stage_sekarang+1),
            ('tipe','=','Non Cash'),
            ('name','=','Dok Diterima')])
        if stage_next.id:
            plafond = self.env['wika.loan.plafond.detail'].search([('id', '=', self.plafond_bank_id.id)])
            for data in plafond:
                use = sum(x.jumlah_pengajuan for x in self)
                plafond.pengajuan = plafond.pengajuan + float(use)
            self.stage_id = stage_next.id
            self.dalam_proses = self.jumlah_pengajuan
            # self.step_approve = 1

    def action_reject_input(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        cek = False
        level=self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'wika.noncash.loan')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
            if not approval_id:
                raise ValidationError(
                'Approval Setting untuk menu Non cash loan tidak ditemukan. Silakan hubungi Administrator!')
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
                'context': {'groups_id': groups_id.id, 'default_ncl_id': self.id},
                'view_id': self.env.ref('wika_noncash_loan.ncl_input_reject_wizard_form').id,
            }
            return action
        else:
            raise ValidationError('User Akses Anda tidak berhak Reject!')

    def action_proses(self):
        stage_default = self.env['wika.loan.stage'].search([
            ('tipe','=','Non Cash'),('name','=','Pembukaan'),
            ('request','=',False)],limit=1)
        _logger.info('CHECKK DEFAULT STAGE Action Proses - Default Stage ID: %s', stage_default.id)
        action = {
            'name': ('NCL Proses'),
            'type': "ir.actions.act_window",
            'res_model': "wika.noncash.loan",
            'view_type': "form",
            'limit': 20,
            'view_mode': "tree,form",
            'view_id': False,
            'views': [
                (self.env.ref('wika_noncash_loan.wika_ncl_proses_view_tree').id, 'tree'),
                (self.env.ref('wika_noncash_loan.wika_ncl_proses_view_form').id, 'form'),
            ],
            'context': {'default_stage_id': stage_default.id},
            'domain': [('stage_id.name', 'not in', ['Pengajuan','Proses Approval'])]
        }
        return action

    @api.depends('jenis_id')
    def _compute_keterangan_html(self):
        for record in self:
            keterangan_html = ''

            if record.jenis_id.nama == 'SCF':
                keterangan_html += '''
                <div style="background-color: aliceblue;">
                    <h4>Keterangan :</h4>
                    <ul>
                        <li>Nilai Tagihan Netto = Nilai Pokok + PPN - Potongan PPh - Potongan Lain</li>
                        <li>Nilai Pengajuan = Nilai Pokok Tagihan - Potongan PPh - Potongan Lain</li>
                    </ul>  
                </div>'''

            elif record.jenis_id.nama == 'SKBDN/LC':
                keterangan_html += '''
                <div style="background-color: aliceblue;">
                    <h4>Keterangan :</h4>
                    <ul>
                        <li>Nilai Pokok = Nilai Progress - Potongan Uang Muka</li>
                        <li>Nilai Tagihan Netto = Nilai Pokok + PPN - Potongan PPh</li>
                        <li>Nilai Pengajuan = Nilai Pokok Tagihan - Potongan PPh</li>
                    </ul>
                </div>'''

            record.keterangan_html = keterangan_html

    def action_pp(self):
        if self.payment_id:
            if self.payment_id.state == 'Lunas':
                raise ValidationError('Loan ini sudah lunas. Tidak dapat diperpanjang!')

        form_id = self.env.ref('wika_noncash_loan.ncl_view_form_pp_id')
        self.tgl_jatuh_tempo_baru=self.tgl_jatuh_tempo
        return {
            'name': 'Perpanjangan',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wika.noncash.loan',
            'view_id': form_id.id,
            'type': 'ir.actions.act_window', 
            'res_id':self.id,        
            'target': 'new',
            'context': {'default_id': self.id} 
        }
    
    
# class WikAuditLog(models.Model):
#     _name = 'wika.ncl.audit.log'
#     _description = 'Audit Log'

#     user_id = fields.Many2one(comodel_name='res.users',string='User')
#     groups_id = fields.Many2one(comodel_name='res.groups',string='Group')
#     date = fields.Datetime(string='Date')
#     description = fields.Char(string='Description')
#     level = fields.Char(string='Level')
#     ncl_id = fields.Many2one(comodel_name='wika.noncash.loan')

    # def action_input(self):
    #     # stage_default = self.env['wika.loan.stage'].search([('tipe','=','Non Cash'),('name','=','Pengajuan'),('request','=',True)],limit=1)
    #     action = {
    #         'name': ('NCL Input'),
    #         'type': "ir.actions.act_window",
    #         'res_model': "wika.noncash.loan",
    #         'view_type': "form",
    #         'limit': 20,
    #         'view_mode': "tree,form",
    #         'view_id': False,
    #         'views': [
    #                 (self.env.ref('wika_noncash_loan.wika_ncl_input_view_tree').id, 'tree'),
    #                 (self.env.ref('wika_noncash_loan.wika_ncl_input_view_form').id, 'form'),

    #                 ],
    #     }

    #     # usr = self.env['res.users'].search([('id', '=', self._uid)])
    #     # for x in usr:
    #     #     if x.branch_ids:
    #     #         action['domain'] = [('branch_id', 'in', [b.id for b in x.branch_ids]),
    #     #                             ('stage_name','in',['Pengajuan','Proses Approval','Approve','Reject'])]
    #     #     else:
    #     #         action['domain'] = [('stage_name','in',['Pengajuan','Proses Approval','Approve','Reject'])]
    #     return action

class WikaNclPembayaran(models.Model):
    _name = 'wika.ncl.pembayaran' 
    _description = 'Non Cash Loan Pembayaran'
    _rec_name = 'loan_id' 
    _inherit = 'mail.thread'
    _order  = 'state asc, id desc'
    
    loan_id = fields.Many2one(comodel_name='wika.noncash.loan', string="Loan",
        ondelete='set null')
    jenis_id                = fields.Many2one(related='loan_id.jenis_id')
    nama_jenis              = fields.Char(related='loan_id.nama_jenis',string="Kriteria",store=True, index=True)
    # nama_tipe_kriteria      = fields.Char(related='loan_id.tipe_jenis_name',string="Tipe Kriteria",store=True)
    jumlah_pengajuan        = fields.Float(related='loan_id.jumlah_pengajuan', string="Nilai Pengajuan",
                                           store = True,group_operator = 'avg')
    plafond_bank_id         = fields.Many2one(related='loan_id.plafond_bank_id', string="Plafond Bank", store=True)
    vendor_id               = fields.Many2one(related='loan_id.vendor_id',string="Vendor") 
    nomor_swift = fields.Char(related='loan_id.no_swift',string="Nomor Swift",store=True) 
    stage_name              = fields.Char(related='loan_id.stage_name',string="Stage Name",store=True) 
    no_swift_akseptasi      = fields.Char(string='Nomor Swift Akseptasi')   
    tgl_swift_akseptasi     = fields.Date(string='Tanggal Swift Akseptasi')
    no_swift_tr             = fields.Char(string='Nomor Swift TR/Perpanjangan')
    tgl_swift_tr            = fields.Date(string='Tanggal Swift TR/Perpanjangan')
    no_swift_tr_baru        = fields.Char(string='Nomor Swift TR/Perpanjangan')
    tgl_swift_tr_baru       = fields.Date(string='Tanggal Swift TR/Perpanjangan')
    bank_id                 = fields.Many2one(related='loan_id.bank_id',string="Bank", index=True, store=True)
    # department_id           = fields.Many2one(related='loan_id.department_id',
    #                           string="Divisi Lama", store=True, index=True, readonly=True)
    branch_id               = fields.Many2one(related='loan_id.branch_id',
                              string="Divisi", store=True, index=True, readonly=True)
    company_currency        = fields.Many2one(related='loan_id.company_currency',
                                              string='Currency')
    currency_id             = fields.Many2one(related='loan_id.currency_id',
                                              string='Currency',store=True)
    # currency_diff           = fields.Many2one(comodel_name="res.currency",string='Currency') 
    kurs_awal               = fields.Float(related='loan_id.kurs',string='Kurs Pembukaan')    
    kurs_baru               = fields.Float(string='Kurs Baru')  
    masa_klaim              = fields.Integer(string='Masa Klaim (Hari)')

    # cur_id                  = fields.Integer(related='loan_id.currency_id.id',store=False)
    nilai_pokok_asing       = fields.Float(string='Pembayaran Pokok Asing')

    nilai_pokok             = fields.Float(string='Pembayaran Pokok')
    nilai_bunga             = fields.Float(string='Nilai Bunga')
    total                   = fields.Float(string='Total', compute='_compute_total')
    # jumlah_bayar            = fields.Float(string='Jumlah Bayar')

    tgl_jatuh_tempo         = fields.Date(string='Tanggal Jatuh Tempo', index=True, required=True)
    tgl_bayar               = fields.Date(string='Tanggal Bayar')
    keterangan              = fields.Char(string='Ket')
    state = fields.Selection(string='Status', selection=[
        ('Belum Dibayar', 'Belum Dibayar'),
        ('Lunas', 'Lunas'),
        ('TR', 'TR'),
        ('Perpanjangan', 'Perpanjangan')
    ], default='Belum Dibayar', index=True)
    cek_pelunasan           = fields.Boolean(string='Apakah Pelunasan dilakukan dengan Bank Lain?')
    new_no_rekening = fields.Many2one(comodel_name='res.partner.bank',
                                  string="No Rekening")
    new_bank_id             = fields.Many2one(comodel_name='res.bank',string='New Bank')
    new_plafond_id          = fields.Many2one(comodel_name='wika.loan.plafond.detail')
    status_akseptasi        = fields.Selection(string='Status Akseptasi', selection=[
                                ('Akseptasi', 'Akseptasi'),
                                ('Tidak Akseptasi', 'Tidak Akseptasi')])            
    project_id               = fields.Many2one(comodel_name='project.project',
                                          string="Proyek", ondelete='set null', index=True)

    nomor_swift_baru = fields.Char(string="Nomor Swift Baru", store=True)
    tgl_swift_baru = fields.Date(string='Tanggal Swift Baru', store=True)
    tgl_jatuh_tempo_baru = fields.Date(string='Tanggal Jatuh Tempo Baru', store=True)
    keterangan_jatuh_tempo = fields.Selection(string='Keterangan Jatuh Tempo',
                                              selection=[('pasti', 'Pasti'), ('tidak_pasti', 'Tidak Pasti')])
    # # Baru
    # tgl_skrg   = fields.Date(string='Tanggal skrg', store=True)
    # # total_h5=fields.Float(string='Total H-5 (Dalam Juta)',compute='compute_total', store=True)
    
    # plaf_id     = fields.Many2one(related='plafond_bank_id.plafond_id',store=True)
    plaf_id     = fields.Many2one('wika.plafond.bank',store=True)
    # Csisa       = fields.Float(string="Total (Dalam Juta)",store=True,compute="_compute_sisa")
    # Gsisa       = fields.Float(related='Csisa', store=True)
    status_comdisc = fields.Selection(string="COMP/DISC", selection=[
        ('Comply', 'Comply'),
        ('Discrepency', 'Discrepency')])
    sel_over= fields.Selection(selection=[
        ('Toleransi', 'Toleransi'),
        ('Overdraft', 'Overdraft')])
    tr_ids = fields.One2many(comodel_name='wika.loan.log.tr', string="History TR",
        inverse_name='pembayaran_id', ondelete='cascade', index="true", copy=False)
    nomor_memorial = fields.Char('Nomor Memorial')
    nilai_akutansi      = fields.Float(string='Nilai Akutansi')

    no_sap = fields.Char('No Doc SAP')
    payment_proposal_id_sap              = fields.Char(string='Payment Proposal Id SAP')
    line_item_sap = fields.Char(string='Line Item SAP')
    fiscal_year_sap = fields.Char(string='Fiscal Year SAP')
    run_date_sap= fields.Date(string='Run Date SAP',copy=False)
    from_sap            = fields.Boolean(string='From SAP',default=False,copy=False)
    upload_to_sap       = fields.Boolean(string='Upload to SAP',default=False)
    send= fields.Boolean(string='Send to SAP',default=False,copy=False)
    identifier          = fields.Char(string='Identifier',copy=False)


    @api.depends('nilai_pokok', 'nilai_bunga')
    def _compute_total(self):
        for record in self:
            record.total = record.nilai_pokok + record.nilai_bunga
    
    @api.onchange('nilai_pokok')
    def onchange_nilai_bunga(self):
        for x in self:
            if x.nilai_pokok and x.loan_id.rate_bunga:
                x.nilai_bunga = ((x.nilai_pokok * x.loan_id.rate_bunga) / 100)
    
    def action_pp(self):
        form_id = self.env.ref('wika_noncash_loan.ncl_view_form_pp_id')
        return {
            'name': 'Perpanjangan',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wika.noncash.loan',
            'view_id': form_id.id,
            'type': 'ir.actions.act_window', 
            'res_id':self.loan_id.id,        
            'target': 'new',
            'context': {'default_id': self.loan_id.id} 
        }    

    def action_tr(self):
        form_id = self.env.ref('wika_noncash_loan.ncl_pembayaran_form_view_tr')
        return {
            'name': 'TR',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wika.ncl.pembayaran',
            'view_id': form_id.id,
            'type': 'ir.actions.act_window', 
            'res_id':self.id,        
            'target': 'new',
            'context': {'default_id': self.id} 
        }

    def tr(self):
        if self.loan_id.nama_jenis == 'SCF' or self.loan_id.nama_jenis == 'SKBDN/LC':
            jenis = self.env['wika.loan.jenis'].search([
                ('nama', '=', self.loan_id.nama_jenis), 
                ('tipe', '=', 'Non Cash')
                ], limit=1)
            
            tgl_formatted = self.tgl_jatuh_tempo_baru
            tgl_mulai = "%s-01-01" % tgl_formatted.year
            tgl_akhir = "%s-12-31" % tgl_formatted.year
        
            stage_next = self.env['wika.loan.stage'].search([
                ('tipe', '=', 'Non Cash'),
                ('name', '=', 'TR')])

            # cek jenis dulu, skbdn tr, else perpanjangan, terus status akseptasi
            if self.nama_jenis == 'SCF':
                if self.state == 'Belum Dibayar':
                    self.state = 'TR'
                    self.loan_id.stage_id = stage_next.id
            else:
                if self.state == 'Belum Dibayar' and self.status_akseptasi == 'Akseptasi':
                    self.state = 'TR'
                    self.loan_id.stage_id = stage_next.id

            log_tr = self.env['wika.loan.log.tr'].search([
                ('pembayaran_id', '=', self.id)])
            ke = 1
            if log_tr:
                for x in log_tr:
                    ke += 1
            today = fields.Date.context_today(self)
            self.env['wika.loan.log.tr'].create({
                'loan_id': self.loan_id.id,
                'ke': ke,
                'pembayaran_id': self.id,
                'no_swift_lama': self.no_swift_tr,
                'tgl_swift_lama': self.tgl_swift_tr,
                'tgl_jatuh_tempo_lama': self.tgl_jatuh_tempo,
                'tgl_eksekusi': today})

            self.no_swift_tr = self.no_swift_tr_baru
            self.tgl_swift_tr = self.tgl_swift_tr_baru
            self.tgl_jatuh_tempo = self.tgl_jatuh_tempo_baru

    def action_bayar_view(self):
        form_id = self.env.ref('wika_noncash_loan.ncl_pembayaran_form_view1')
        return {
            'name': 'Form Pembayaran',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wika.ncl.pembayaran',
            'view_id': form_id.id,
            'type': 'ir.actions.act_window',
            'res_id':self.id,
            'context': {'default_id': self.id},
            'target': 'new',
        }  

    @api.depends('plafond_bank_id.terpakai')
    def bayar(self):          
        today = fields.Date.context_today(self)
        stage_next = self.env['wika.loan.stage'].search([
            ('tipe','=','Non Cash'),
            ('name','=','TR')])

        loan_obj = self.env['wika.noncash.loan']
        loan_pembayaran_obj = self.env['wika.ncl.pembayaran']
        if  self.cek_pelunasan == True and self.new_plafond_id:  
            self.plafond_bank_id.terpakai = self.plafond_bank_id.terpakai - self.nilai_pokok
            self.plafond_bank_id.plafond_id.terpakai = sum(x.terpakai for x in self.plafond_bank_id.plafond_id.plafond_ids)
            self.plafond_bank_id.sisa = self.plafond_bank_id.nilai - self.plafond_bank_id.nilai_book - self.plafond_bank_id.terpakai
            self.plafond_bank_id.plafond_id.sisa = self.plafond_bank_id.plafond_id.jumlah - self.plafond_bank_id.plafond_id.terpakai

            self.new_plafond_id.terpakai = self.new_plafond_id.terpakai + self.nilai_pokok
            self.new_plafond_id.plafond_id.terpakai =  sum(x.terpakai for x in self.new_plafond_id.plafond_id.plafond_ids)
            self.new_plafond_id.sisa = self.new_plafond_id.nilai -  self.new_plafond_id.nilai_book- self.new_plafond_id.terpakai
            self.new_plafond_id.plafond_id.sisa = self.new_plafond_id.plafond_id.jumlah - self.new_plafond_id.plafond_id.terpakai - self.new_plafond_id.plafond_id.nilai_book

            self.loan_id.sisa_outstanding -= self.nilai_pokok

            state_sebelumnya=self.state
            self.state = 'Lunas'
            self.tgl_bayar  = today
            swift_formatted = datetime.strptime(self.tgl_swift_baru, '%Y-%m-%d')
            data = loan_obj.create({
                'bank_id': self.new_bank_id.id,
                'tgl_pembukaan':self.loan_id.tgl_pembukaan,
                'jenis_id' : self.loan_id.jenis_id.id,
                'tgl_swift':self.tgl_swift_baru,
                'tgl_mulai' : self.tgl_swift_baru,
                'tgl_akhir' : swift_formatted+ timedelta(days=self.loan_id.tenor),
                'tgl_mulai_perkiraan': self.tgl_swift_baru,
                'tgl_akhir_perkiraan': swift_formatted+ timedelta(days=self.loan_id.tenor),
                'no_swift':self.nomor_swift_baru,
                'currency_id' : self.loan_id.currency_id.id,
                'plafond_bank_id': self.new_plafond_id.id,
                'jumlah_pengajuan': self.nilai_pokok,
                'rate_bunga': self.loan_id.rate_bunga,
                'tipe_jenis': self.loan_id.tipe_jenis.id,
                'branch_id': self.loan_id.branch_id.id,
                'projek_id': self.loan_id.projek_id.id or False,
                'vendor_id': self.loan_id.vendor_id.id,
                'nomor_surat': self.loan_id.nomor_surat,
                'tenor': self.loan_id.tenor,
                'stage_id' : stage_next.id,
                'no_rekening':self.new_no_rekening.id,
                'sisa_outstanding':self.nilai_pokok,
                'catatan': "Loan dari pembayaran lain."
                    "\nBank : "+self.bank_id.name+
                    "\nNomor Loan : "+self.loan_id.name+
                    "\nNomor Swift : " + str(self.no_swift_akseptasi) or str(self.loan_id.no_swift)
                })
            self.keterangan = "Dengan Bank Lain "+data.name
            loan_pembayaran_obj.create({
                'loan_id':data.id,
                'bank_id': self.new_bank_id.id,
                'state': state_sebelumnya,
                'tgl_jatuh_tempo': self.tgl_jatuh_tempo_baru,
                'nama_jenis': self.nama_jenis,
                'state': 'TR',
                'stage_name': stage_next.name,              
                'currency_id': self.loan_id.currency_id.id,
                'plafond_bank_id': self.new_plafond_id.id,
                'nilai_pokok': self.nilai_pokok,
                'total': self.total,
                'branch_id': self.loan_id.branch_id.id,
                'projek_id': self.projek_id.id or False,
                'plaf_id': self.new_plafond_id.plafond_id.id,
                'Csisa': self.Csisa,
                'Gsisa': self.Gsisa,
                'nama_tipe_kriteria': self.nama_tipe_kriteria
            })
        elif self.cek_pelunasan != True:
            self.new_plafond_id = None  
            self.new_bank_id = None                       
            self.plafond_bank_id.terpakai = self.plafond_bank_id.terpakai - self.nilai_pokok 
            self.plafond_bank_id.plafond_id.terpakai = sum(x.terpakai for x in self.plafond_bank_id.plafond_id.plafond_ids)                                
            self.plafond_bank_id.sisa = self.plafond_bank_id.nilai - self.plafond_bank_id.nilai_book - self.plafond_bank_id.terpakai
            self.plafond_bank_id.plafond_id.sisa = self.plafond_bank_id.plafond_id.jumlah - self.plafond_bank_id.plafond_id.terpakai - self.new_plafond_id.plafond_id.nilai_book
            self.state = 'Lunas'
            self.tgl_bayar  = today
            self.loan_id.sisa_outstanding-=self.nilai_pokok


    @api.depends('loan_id.plafond_bank_id.terpakai')
    def lunas(self):
        today = fields.Date.today()
        today_formatted = datetime.strptime(today, '%Y-%m-%d')
        for x in self:
            if x.nilai_pokok:
                x.plafond_bank_id.terpakai = x.plafond_bank_id.terpakai - x.nilai_pokok
            x.plafond_bank_id.sisa = x.plafond_bank_id.nilai - x.plafond_bank_id.terpakai
            x.plafond_bank_id.plafond_id.terpakai = sum(x.terpakai for x in self.plafond_bank_id.plafond_id.plafond_ids)                                
            x.plafond_bank_id.plafond_id.sisa = x.plafond_bank_id.plafond_id.jumlah - x.plafond_bank_id.plafond_id.terpakai        
        self.state = 'Lunas'
        self.tgl_bayar  = today_formatted
        self.loan_id.sisa_outstanding -= self.nilai_pokok


    def lunas_auto(self):
        today = fields.Date.today()                      
        ncl_tempo = self.env['wika.noncash.loan'].search([
            ('nama_jenis', '=', 'BG'),
            ('payment_id.state','=','Belum Dibayar'),
            ('tgl_jatuh_tempo','<',today)])
        for x in ncl_tempo:
            if ncl_tempo:
                x.plafond_bank_id.terpakai = x.plafond_bank_id.terpakai - x.jumlah_pengajuan               
                x.plafond_bank_id.sisa = x.plafond_bank_id.nilai - x.plafond_bank_id.terpakai - x.plafond_bank_id.nilai_book
                x.plafond_bank_id.plafond_id.terpakai = x.plafond_bank_id.plafond_id.terpakai - x.payment_id.nilai_pokok              
                x.plafond_bank_id.plafond_id.sisa = x.plafond_bank_id.plafond_id.jumlah - x.plafond_bank_id.plafond_id.terpakai  - x.plafond_bank_id.plafond_id.nilai_book       
        
                x.payment_id.state = 'Lunas'
                x.payment_id.keterangan = 'Auto Payment'
                x.payment_id.tgl_bayar  = today


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
    
class WikaNclApprovalLine(models.Model):
    _name = 'wika.noncash.loan.approval.line'

    ncl_id = fields.Many2one('wika.noncash.loan', string='')
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    groups_id = fields.Many2one('res.groups', string='Groups', readonly=True)
    date = fields.Datetime('Date', readonly=True)
    note = fields.Char('Note', readonly=True)