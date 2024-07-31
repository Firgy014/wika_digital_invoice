from odoo import models, fields, api
from datetime import datetime
import pytz
from pytz import timezone

class WikaLoanPrognosa(models.Model):
    _name           = 'wika.loan.prognosa'
    _description    = 'wika loan prognosa'
    _inherit        = 'mail.thread'

    @api.model
    def get_default_year(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta')).year

    @api.model
    def _get_default_mulai(self):
        mulai = "%s-01-01"%self.get_default_year()
        return mulai

    @api.model
    def _get_default_akhir(self):
        mulai = "%s-12-31" % self.get_default_year()
        return mulai

    name = fields.Char(index=True, compute="_compute_field")
    branch_id = fields.Many2one('res.branch', string='Divisi')
    department_id = fields.Many2one('hr.department', string='Divisi Lama')
    bank_id = fields.Many2one('res.bank',string='Bank')
    tipe_id = fields.Many2one('wika.loan.jenis', string='Jenis')
    tgl_mulai = fields.Date(string='Tanggal Mulai', default=_get_default_mulai)
    tgl_akhir = fields.Date(string='Tanggal Akhir', default=_get_default_akhir)
    active = fields.Boolean(string="Active",default=True, store=True)
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)
    prognosa_ids = fields.One2many('wika.loan.prognosa.line',  
        ondelete='cascade', inverse_name='prognosa_id')

    @api.depends('branch_id', 'tgl_mulai', 'tgl_akhir', 'bank_id', 'tipe_id')
    def _compute_field(self):
        for record in self:
            if record.branch_id and record.bank_id and record.tipe_id and record.tgl_mulai and record.tgl_akhir:
                tahun_mulai = datetime.strptime(record.tgl_mulai.strftime('%Y-%m-%d'), '%Y-%m-%d')
                tahun_akhir = datetime.strptime(record.tgl_akhir.strftime('%Y-%m-%d'), '%Y-%m-%d')
                if tahun_mulai.year == tahun_akhir.year:
                    tahun = "%s" % tahun_mulai.year
                else:
                    tahun = "%s - %s" % (tahun_mulai.year, tahun_akhir.year)
                record.name = "%s/%s/%s/%s" % (record.branch_id.code, record.bank_id.name, record.tipe_id.nama, tahun)
            else:
                record.name = ""

    def update_branch(self):
        ncl=self.env['wika.loan.prognosa'].search([])
        for x in ncl:
            branch=self.env['res.branch'].search([('code','=',x.department_id.code)],limit=1)
            x.branch_id=branch.id

class WikaLoanPrognosaLine(models.Model):
    _name = 'wika.loan.prognosa.line'
    _description = 'wika loan prognosa line'

    prognosa_id = fields.Many2one(comodel_name='wika.loan.prognosa')
    bulan = fields.Selection([
        ('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'),
        ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'),
        ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember')],
        string='Bulan')
    tgl_mulai = fields.Date(string='Tanggal Mulai')
    tgl_akhir = fields.Date(string='Tanggal Akhir')
    nilai_pembukaan = fields.Float(string='Nilai Pembukaan')
    nilai_tr = fields.Float(string='Nilai TR')
    terpakai = fields.Float(string="Terpakai Pembukaan", compute='_compute_terpakai')
    terpakai_tr = fields.Float(string="Terpakai TR", compute='_compute_terpakai_tr')

    def replace_lower(self):
        if self.bulan:
            value = dict(self._fields['bulan'].selection).get(self.bulan)
            xvalue = value.replace('.', '_').replace(' ', '_').lower()
            return xvalue
        return None

    def _compute_terpakai(self):
        for x in self:
            # Gunakan tgl_mulai langsung karena sudah bertipe datetime.date
            tgl_formatted = x.prognosa_id.tgl_mulai
            
            # Konversi bulan ke integer
            bulan_int = int(x.bulan)
            bln_next = bulan_int + 1
            year_next = tgl_formatted.year
            if bln_next > 12:
                bln_next -= 12
                year_next += 1

            # Format tanggal menjadi string
            tgl_awal = "{}-{:02d}-01".format(tgl_formatted.year, bulan_int)
            tgl_akhir = "{}-{:02d}-01".format(year_next, bln_next)

            loan = self.env['wika.noncash.loan'].search([
                ('tgl_pembukaan', '>=', tgl_awal),
                ('tgl_pembukaan', '<', tgl_akhir),
                ('nama_jenis', '=', x.prognosa_id.tipe_id.nama),
                ('bank_id', '=', x.prognosa_id.bank_id.id),
                ('branch_id', '=', x.prognosa_id.branch_id.id),
                ('stage_name', 'not in', ['Pengajuan', 'Proses Approval', 'Reject', 'Ditolak', 'Tidak Akseptasi', 'Cancel', 'Perpanjangan', 'TR'])
            ])
            jumlah = 0
            for z in loan:
                jumlah += z.jumlah_pengajuan

            x.terpakai = jumlah

    def _compute_terpakai_tr(self):
        for x in self:
            tgl_formatted = x.prognosa_id.tgl_mulai
            bulan_int = int(x.bulan)
            bln_next = bulan_int + 1
            year_next = tgl_formatted.year
            if bln_next > 12:
                bln_next -= 12
                year_next += 1

            # tinggal cek yang tr nya. Berarti cari juga yang stage name nya not in tr (tbd)

            tgl_awal = "{}-{:02d}-01".format(tgl_formatted.year, bulan_int)
            tgl_akhir = "{}-{:02d}-01".format(year_next, bln_next)

            pembayaran = self.env['wika.ncl.pembayaran'].search([
                ('tgl_jatuh_tempo', '>=', tgl_awal),
                ('tgl_jatuh_tempo', '<', tgl_akhir),
                ('nama_jenis', '=', x.prognosa_id.tipe_id.nama),
                ('bank_id', '=', x.prognosa_id.bank_id.id),
                ('branch_id', '=', x.prognosa_id.branch_id.id),
                ('state', '=', 'TR')
            ])
            jumlah = 0
            for z in pembayaran:
                jumlah += z.nilai_pokok

            x.terpakai_tr = jumlah