from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import pytz
from pytz import timezone
import json

def get_years():
    year_list = []
    for i in range(2018, 2100):
        year_list.append((str(i), str(i)))
    # print("before returned", year_list)
    # wakwaw

    return year_list

def get_default_year(self):
    return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta')).year

def get_default_month(self):
    return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta')).month

class WikaMCSBudgetBulan(models.Model):
    _name = 'wika.mcs.budget.bulan'
    _rec_name = 'coa_id'

    coa_id = fields.Many2one(string='COA', comodel_name='wika.mcs.budget.coa', index=True)
    tahun = fields.Selection(string='Tahun', related='coa_id.tahun')
    kode_coa = fields.Many2one(string='Kode COA', related='coa_id.kode_coa')
    department = fields.Many2one(string='Department', related='coa_id.department')
    biro = fields.Many2one(string='Biro', related='coa_id.biro')
    state = fields.Selection(string='Status', related='coa_id.state')
    tipe_budget = fields.Selection(string='Tipe Budget', related='coa_id.tipe_budget')

    total_anggaran = fields.Float(string='Rencana (RKAP)', compute='_compute_total_anggaran',store=True)
    anggaran_sd = fields.Float(string="Akumulasi Anggaran", compute='_compute_anggaran_sd')
    sisa_anggaran = fields.Float(string='Sisa Anggaran', compute='_compute_sisa_anggaran', store=True)
    terpakai_vb = fields.Float(string="Realisasi Vendor Bills", compute='_compute_terpakai_vendorbills')
    terpakai_vb_sd = fields.Float(string="Akumulasi Realisasi Vendor Bills", compute='_compute_terpakai_vendorbills_sd')
    persen = fields.Float(string="% RI Terhadap RA", compute="_compute_percent", store=True)
    persen_hd = fields.Float(string="Persen", compute="_compute_percent_hd")
    bulan = fields.Selection([('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'),
                              ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'),
                              ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember')],
                             string='Bulan', default=get_default_month, index=True)
    prognosa = fields.Float(string='Prognosa', compute='_compute_total_anggaran', store=True, default=0.0)
    persentase_ri_prog = fields.Float(string='% RI Terhadap Prognosa', store=True, compute='_compute_persen_ri_prog', default=0.0)
    persentase = fields.Float(string='% RKAP Terhadap Prognosa Tahun Lalu', store=True, compute='_compute_persen', default=0.0)
    rencana_sebelumnya = fields.Float(string='Prognosa Tahun Sebelumnya', compute='_compute_rencana', store=True)

    def replace_lower(self):
        if self.bulan:
            value = dict(self._fields['bulan'].selection).get(self.bulan)
            xvalue = str(value).replace('.', '_').replace(' ', '_').lower()
            return xvalue
        return None

    @api.depends('coa_id.kode_coa','coa_id.department','coa_id.biro')
    def _compute_rencana(self):
        for x in self:
            if x.coa_id.biro:
                anggaran = self.env['wika.mcs.budget.bulan'].search(
                    [('kode_coa', '=', x.coa_id.kode_coa.id), ('bulan', '=', x.bulan),
                    ('state', '=', x.coa_id.state),('tahun', '=', x.coa_id.tahun-1),
                    ('tipe_budget', '=', x.coa_id.tipe_budget),
                    ('department', '=', x.coa_id.department.id),
                    ('biro', '=', x.coa_id.biro.id)])
            else:
                 anggaran = self.env['wika.mcs.budget.bulan'].search(
                    [('kode_coa', '=', x.coa_id.kode_coa.id), ('bulan', '=', x.bulan),
                    ('state', '=', x.coa_id.state),('tahun', '=', x.coa_id.tahun-1),
                    ('tipe_budget', '=', x.coa_id.tipe_budget),
                    ('department', '=', x.coa_id.department.id)])

            if anggaran:
                rencana_sebelumnya = 0
                for z in anggaran:
                    print (z)
                    rencana_sebelumnya += z.prognosa
                x.rencana_sebelumnya = rencana_sebelumnya

    @api.depends('rencana_sebelumnya', 'total_anggaran')
    def _compute_persen(self):
        for x in self:
            if x.rencana_sebelumnya > 0 and x.total_anggaran > 0:
                x.persentase = x.total_anggaran / x.rencana_sebelumnya * 100
            else:
                x.persentase = 0.0

    @api.depends('terpakai_vb', 'prognosa')
    def _compute_persen_ri_prog(self):
        for x in self:
            if x.terpakai_vb > 0 and x.prognosa > 0:
                x.persentase_ri_prog = x.terpakai_vb / x.prognosa * 100
            else:
                x.persentase_ri_prog =0.0
    
    @api.depends('coa_id.total_anggaran', 'terpakai_vb')
    def _compute_percent_hd(self):
        for x in self:
            if x.anggaran_sd > 0:
                x.persen_hd = x.terpakai_vb_sd / x.anggaran_sd * 100

    @api.depends('total_anggaran', 'terpakai_vb')
    def _compute_percent(self):
        for x in self:
            if x.total_anggaran > 0:
                x.persen = x.terpakai_vb / x.total_anggaran * 100

    @api.depends('total_anggaran')
    def _compute_terpakai_vendorbills_sd(self):
        for x in self:
            akumulasi = 0
            line = self.env['wika.mcs.budget.bulan'].search([('bulan', '<=', x.bulan), ('coa_id', '=', x.coa_id.id)])
            for x in line:
                akumulasi += x.terpakai_vb
            x.terpakai_vb_sd = akumulasi

    @api.depends('total_anggaran','coa_id.department','coa_id.biro')
    def _compute_terpakai_vendorbills(self):
        for x in self:
            terpakai = self.global_compute_terpakai_vendorbills(x.bulan, x.tahun, str(x.kode_coa.id), str(x.department.id), str(x.department.biro),str(x.biro.id), 'Bulan Ini')
            x.terpakai_vb = terpakai
    
    @api.depends('total_anggaran','terpakai_vb_sd')
    def _compute_sisa_anggaran(self):
        for x in self:
            x.sisa_anggaran = x.total_anggaran - x.terpakai_vb_sd

    @api.depends('total_anggaran')
    def _compute_anggaran_sd(self):
        for x in self:
            akumulasi = 0
            line = self.env['wika.mcs.budget.bulan'].search([('bulan', '<=', x.bulan), ('coa_id', '=', x.coa_id.id)])
            for x in line:
                akumulasi += x.total_anggaran
            x.anggaran_sd = akumulasi

    @api.depends('coa_id.detail_ids.line_ids.anggaran')
    def _compute_total_anggaran(self):
        for x in self:
            anggaran = self.env['wika.mcs.budget.coa.detail.line'].search(
                [('coa_id', '=', x.coa_id.id), ('bulan', '=', x.bulan)])
            if anggaran:
                total_anggaran = 0
                for z in anggaran:
                    total_anggaran += z.anggaran
                x.total_anggaran = total_anggaran
                x.prognosa = total_anggaran

class WikaMCSBudgetCOA(models.Model):
    _name = 'wika.mcs.budget.coa'
    _description = 'Master Budgetting'

    @api.model
    def _getdefault_branch(self):
        user = self.env.user
        branch_id = user.branch_id
        if branch_id:
            if branch_id.biro:
                return branch_id.parent_id.id
            else:
                return branch_id.id
        return False

    grup_akun = fields.Many2one('wika.mcs.budget.parent', string="Grup", index=True)
    tahun = fields.Selection(get_years(), string='Tahun')
    kode_coa = fields.Many2one('account.account', string="Kode COA")
    department = fields.Many2one('res.branch', string='Divisi', copy=False, default=_getdefault_branch)
    biro = fields.Many2one('res.branch', string='Department', copy=False)
    total_anggaran = fields.Float(string='Total Anggaran FMS', compute='_compute_total_anggaran', store=True)
    total_anggaran_sap = fields.Float(string='Total Anggaran SAP')

    detail_ids = fields.One2many('wika.mcs.budget.coa.detail', 'coa_id', string="Detail Pekerjaan", index=True, ondelete='cascade', copy=True)
    detail_ids2 = fields.One2many('wika.mcs.budget.bulan', 'coa_id', string="Detail Per Bulan", index=True, ondelete='cascade', copy=True)
    check_biro = fields.Boolean(compute="_cek_biro")
    tipe_budget = fields.Selection([('capex', 'Capex'), ('opex', 'Opex')], string='Tipe Budget')
    tipe_budget_id = fields.Many2one('wika.tipe.budget', string='Tipe Budget')

    terpakai_vb = fields.Float(string='Terpakai Vendor Bills', compute='_compute_terpakai')
    persen = fields.Float(string='Persen', compute='_compute_persen')
    sisa = fields.Float(string='Sisa', compute='_compute_sisa')
    state = fields.Selection([('Draft', 'Draft'), ('Confirm', 'RKAP'), ('Review', 'Review')], string='Status', default='Draft', index=True)
    sequence = fields.Integer(string='Sequence')
    total_depres = fields.Float(string="Nilai Depresiasi Per Tahun", compute='_compute_depresiasi')
    bulan_review = fields.Selection([('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'), ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'), ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember')], string='Month')

    aktif = fields.Boolean(string='Active', default=True)
    asset_category_id = fields.Many2one('account.asset', string='Kategori Asset')
    from_sap = fields.Boolean(string='From SAP', default=False)
    terpakai_sap = fields.Float(string='Terpakai SAP')
    available_amount_sap = fields.Float(string='Available Amount SAP')

    def replace_lower(self):
        if self.bulan_review:
            value = dict(self._fields['bulan_review'].selection).get(self.bulan_review)
            xvalue = str(value).replace('.', '_').replace(' ', '_').lower()
            return xvalue
        return None

    def unlink(self):
        for x in self:
            if x.state != 'Draft':
                raise UserError(_('Data yang sudah di validate tidak boleh dihapus!'))
            x.detail_ids2.unlink()
            x.detail_ids.unlink()
        return super(WikaMCSBudgetCOA, self).unlink()

    @api.onchange('kode_coa')
    def _onchange_kode_coa(self):
        self.grup_akun = None
        if self.kode_coa:
            spl = self.kode_coa.code[0:4]
            grup = self.env['wika.mcs.budget.parent'].search([('name','ilike',spl)],limit=1)
            self.grup_akun=grup.id

    @api.onchange('tipe_budget')
    def _domain_account(self):
        domain = {}
        for x in self:
            if x.tipe_budget == 'opex':
                account = self.env['account.account'].search([('company_id', '=', 1)])

                y = [data.id for data in account if len(data.code)>=7]
                domain = {'domain': {
                    'kode_coa': [('id', 'in', y)],
                }}
            return domain

    @api.onchange('tipe_budget_id')
    def change_tipe(self):
        for x in self:
            if x.tipe_budget_id.code=='opex':
                x.tipe_budget='opex'
            if x.tipe_budget_id.code=='capex':
                x.tipe_budget='capex'
            if x.tipe_budget_id.code=='bad':
                x.tipe_budget='bad'

    def _compute_depresiasi(self):
        for x in self:
            assets = self.env['account.asset'].search([
                ('account_asset_id', '=', x.kode_coa.id),
                ('branch_id', '=', x.department.id),
                ('biro', '=', x.biro.id)
            ], limit=1)
            total_depres = 0
            awal_tahun = "%s-01-01" % x.tahun
            next = x.tahun + 1
            akhir_tahun = "%s-01-01" % next
            for asset in assets:
                depres = self.env['account.move'].search([
                    ('asset_id', '=' , asset.id),
                    ('asset_depreciation_beginning_date', '>=' , awal_tahun),
                    ('asset_depreciation_beginning_date', '<', akhir_tahun)
                ])
                nilai = 0
                for z in depres:
                    nilai += z.amount

                total_depres += nilai

            x.total_depres = total_depres

    def set_to_draft(self):
        for x in self:
            x.state = 'Draft'

    def confirm(self):
        self.state = 'Confirm'

    def get_bulan(self,tahun):
        for x in self:
            year = pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta')).year

            if tahun < year:
                bulan = 12
            else:
                bulan = pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta')).month

            return bulan

    @api.depends('detail_ids2.terpakai_vb')
    def _compute_terpakai(self):
        for x in self:
            x.terpakai_vb = sum(z.terpakai_vb for z in x.detail_ids2)

    @api.depends('department')
    def _cek_biro(self):
        for x in self:
            if x.department:
                biro = self.env['res.branch'].search([('parent_id', '=', x.department.id)])
                if biro:
                    x.check_biro = True
                else:
                    x.check_biro = False
            else:
                x.check_biro = False

    @api.depends('terpakai_sap','terpakai_vb')
    def _compute_sisa(self):
        for x in self:
            x.sisa = x.total_anggaran_sap - x.terpakai_vb - x.terpakai_sap

    def _compute_persen(self):
        for x in self:
            bulan = x.get_bulan(x.tahun)
            blns = self.env['wika.mcs.budget.bulan'].search([('coa_id','=',x.id),('bulan','=',bulan)],limit=1)
            x.persen = blns.persen_hd

    @api.depends('detail_ids.total_anggaran')
    def _compute_total_anggaran(self):
        for x in self:
            anggaran = 0
            for z in x.detail_ids:
                anggaran += z.total_anggaran
            x.total_anggaran = anggaran

    def act_generate(self):
        for x in self.detail_ids:
            if x.status_generate==False:
                for i in range(12):
                    self.env['wika.mcs.budget.coa.detail.line'].create({
                        'detail_id': x.id,
                        'bulan': i + 1,
                        'sequence': i + 1,
                    })
                x.status_generate = True
        if not self.detail_ids2:
            for i in range(12):
                self.env['wika.mcs.budget.bulan'].create({
                    'coa_id': self.id,
                    'bulan': i + 1,
                })

    def name_get(self):
        res = []
        for record in self:
            biro=""
            if record.biro:
                biro = " - %s"%record.biro.code
            tit = "[%s] [%s%s] [%s - %s]" % (record.tahun, record.department.code,biro,record.kode_coa.code,record.kode_coa.name)
            res.append((record.id, tit))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=1000):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            args = ['|', ('code', operator, name), ('name', operator, name)] + args
        categories = self.search(args, limit=limit)
        return categories.name_get()

class WikaMCSBudgetParent(models.Model):
    _name = 'wika.mcs.budget.parent'

    name = fields.Char(string="Nama Grup")
    parent = fields.Many2one(comodel_name='wika.mcs.budget.parent', string="Parent")
    sequence = fields.Integer(string='Sequence')

class WikaMCSBudgetCOADetail(models.Model):
    _name = 'wika.mcs.budget.coa.detail'
    _rec_name = 'pekerjaan'

    coa_id = fields.Many2one(string="ID Coa", ondelete='cascade', comodel_name='wika.mcs.budget.coa', index=True)
    pekerjaan = fields.Many2one(string='Nama Pekerjaan', comodel_name='product.product')
    vol = fields.Float(string='Volume')
    satuan = fields.Char(string='Satuan')
    harga_satuan = fields.Float(string='Harga Satuan')
    anggaran = fields.Float(string='Anggaran', compute='_compute_anggaran',store=True)
    is_beban = fields.Boolean(string="Dibebankan")
    beban = fields.Float(string="Beban (%)")
    total_rencana = fields.Float(string='Total Rencana Anggaran', compute='_compute_total_rencana')
    total_anggaran = fields.Float(string='Total Anggaran', compute='_compute_total_anggaran', store=True)
    total_beban = fields.Float(string='Total Beban', compute='_compute_total_beban', store=True)
    line_ids = fields.One2many(string="Bulan", comodel_name='wika.mcs.budget.coa.detail.line',
                               inverse_name='detail_id',
                               index=True, ondelete='cascade', copy=True)
    beban_ids = fields.One2many(string="Beban", comodel_name='wika.mcs.budget.coa.detail.beban',
                               inverse_name='detail_id',
                               index=True, ondelete='cascade', copy=True)
    status_generate=fields.Boolean(string="Status Generate", copy=True, default=False)
    total_bulan=fields.Integer(compute='_compute_total_bulan')
    tipe_budget= fields.Selection(related='coa_id.tipe_budget')

    @api.onchange('tipe_budget')
    def _domain_product(self):
        domain = {}
        for x in self:
            if x.tipe_budget == 'opex' and x.coa_id.kode_coa:
                product = self.env['product.product'].search([('property_account_expense_id', '=', x.coa_id.kode_coa.id)])

                y = [prod.id for prod in product]
                domain = {'domain': {
                    'pekerjaan': [('id', 'in', y)],
                }}
            return domain
        
    def unlink(self):
        for x in self:
            x.line_ids.unlink()
            x.beban_ids.unlink()
        return super(WikaMCSBudgetCOADetail, self).unlink()

    @api.depends('tipe_budget')
    def _compute_total_rencana(self):
        for x in self:
            if x.tipe_budget != 'bad':
                x.total_rencana = x.vol * x.harga_satuan
            elif x.tipe_budget == 'bad':
                x.total_rencana = x.harga_satuan+x.total_beban

    @api.depends('line_ids.anggaran')
    def _compute_total_anggaran(self):
        for x in self:
            anggaran = 0
            for z in x.line_ids:
                anggaran += z.anggaran
            x.total_anggaran = anggaran

    @api.onchange('anggaran','is_beban')
    def _onchange_anggaran(self):
        for x in self:
            if x.is_beban==True and x.anggaran:
                x.beban = x.anggaran / x.total_rencana  * 100

    @api.depends('beban_ids.anggaran')
    def _compute_total_beban(self):
        for x in self:
            anggaran = 0
            for z in x.beban_ids:
                anggaran += z.anggaran
            x.total_beban = anggaran

    @api.depends('vol','harga_satuan','beban')
    def _compute_anggaran(self):
        for x in self:
            if x.beban > 0.0:
                x.anggaran = (x.beban/100) * x.harga_satuan * x.vol
            else:
                x.anggaran = x.vol * x.harga_satuan

    @api.onchange('anggaran', 'total_rencana','total_beban','tipe_budget')
    def onchange_anggaran_beban(self):
        if self.tipe_budget != 'bad':
            if self.total_rencana < (self.total_beban + self.anggaran) :
                raise ValidationError('Total beban melebihi total rencana yang ditentukan.'
                                      '(lebih %.2f)!' % (
                                              (self.total_beban + self.anggaran) - self.total_rencana ))
    @api.depends('line_ids')
    def _compute_total_bulan(self):
        for x in self:
            total = 0
            for z in x.line_ids:
                total += 1
            x.total_bulan = total

    def act_generate(self):
        for i in range(12):
            cek = self.env['wika.mcs.budget.coa.detail.line'].search([('bulan', '=', i + 1), ('detail_id', '=', self.id)], limit=1)
            if not cek:
                self.env['wika.mcs.budget.coa.detail.line'].create({
                    'detail_id': self.id,
                    'bulan': i + 1,
                    'sequence': i + 1,
                })
                self.status_generate=True

    def act_bulan(self):
        for x in self:
            if x.coa_id:
                if x.coa_id.state != 'Draft':
                    form_id = self.env.ref('wika_budget_management.budget_form_view_3_2_2')
                    ctx = {}
                else:
                    form_id = self.env.ref('wika_budget_management.budget_form_view_3_2')
                    ctx = {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true', 'default_id': self.id}

                return {
                    'name': 'Per Bulan',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'wika.mcs.budget.coa.detail',
                    'view_id': form_id.id,
                    'type': 'ir.actions.act_window',
                    'res_id': x.id,
                    'target': 'current',
                    'context': ctx
                }

    def act_beban(self):
        for x in self:
            if x.coa_id:
                if x.coa_id.state != 'Draft':
                    form_id = self.env.ref('wika_budget_management.budget_form_view_3_3_2')
                    ctx = {}
                else:
                    form_id = self.env.ref('wika_budget_management.budget_form_view_3_3')
                    ctx = {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true', 'default_id': self.id}

                return {
                    'name': 'Pembebanan',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'wika.mcs.budget.coa.detail',
                    'view_id': form_id.id,
                    'type': 'ir.actions.act_window',
                    'res_id': x.id,
                    'target': 'current',
                    'context': ctx
                }
            
class WikaMCSBudgetCOADetailBeban(models.Model):
    _name = 'wika.mcs.budget.coa.detail.beban'

    detail_id = fields.Many2one(string="ID Detail", ondelete='cascade', comodel_name='wika.mcs.budget.coa.detail', index=True)
    coa_id = fields.Many2one(comodel_name='wika.mcs.budget.coa', related='detail_id.coa_id', readonly=True)
    tipe_budget = fields.Selection(related='detail_id.tipe_budget')

    total_rencana = fields.Float(related='detail_id.total_rencana')
    branch_id = fields.Many2one(string="Divisi", comodel_name='res.branch', index=True)
    account_id = fields.Many2one(string="COA SAP", comodel_name='account.account', index=True, domain=[('company_id', '=', 1)])

    persen = fields.Float(string='Persen')
    anggaran = fields.Float(string='Anggaran', index=True)

    @api.onchange('persen','total_rencana')
    def _onchange_persen(self):
        if self.persen > 0 and self.total_rencana > 0:
            self.anggaran = self.total_rencana * self.persen / 100

    @api.onchange('anggaran','total_rencana')
    def _onchange_anggaran(self):
        if self.anggaran > 0 and self.total_rencana > 0:
            self.persen = self.anggaran / self.total_rencana * 100

class WikaMCSBudgetCOADetailLine(models.Model):
    _name = 'wika.mcs.budget.coa.detail.line'

    detail_id = fields.Many2one(string="ID Detail", ondelete='cascade', comodel_name='wika.mcs.budget.coa.detail', index=True)
    coa_id = fields.Many2one(string="ID Budget", related='detail_id.coa_id')
    account_id = fields.Many2one(string="Kode Perkiraan", related='detail_id.coa_id.kode_coa')
    tahun = fields.Selection(string="Tahun", related='detail_id.coa_id.tahun')
    state = fields.Selection(string="State", related='detail_id.coa_id.state')
    tipe_budget = fields.Selection(string="Tipe Budget", related='detail_id.coa_id.tipe_budget')
    department_id = fields.Many2one(string="Department", related='detail_id.coa_id.department')
    biro_id = fields.Many2one(string="Biro", related='detail_id.coa_id.biro')
    sequence = fields.Integer(string='Sequence')
    anggaran = fields.Float(string='Anggaran')
    prognosa = fields.Float(string='Prognosa')
    bulan = fields.Selection([('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'),
                              ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'),
                              ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember')],
                             string='Bulan',index=True)

    def replace_lower(self):
        if self.bulan:
            value = dict(self._fields['bulan'].selection).get(self.bulan)
            xvalue = str(value).replace('.', '_').replace(' ', '_').lower()
            return xvalue
        return None

class WikaMCSBudgetPrint(models.TransientModel):
    _name = 'wika.mcs.budget.print'

    bulan = fields.Selection([('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'),
                              ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'),
                              ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember'), ],
                             string='Month', default=get_default_month)
    tahun = fields.Selection(get_years(), string='Year', default=get_default_year)
    department = fields.Many2one(comodel_name='res.branch', string='Divisi')
    check_biro = fields.Boolean(compute="_cek_biro")
    biro = fields.Many2one(comodel_name='res.branch', string='Department')

    def replace_lower(self):
        if self.bulan:
            value = dict(self._fields['bulan'].selection).get(self.bulan)
            xvalue = str(value).replace('.', '_').replace(' ', '_').lower()
            return xvalue
        return None

    @api.onchange('department')
    def domain_department(self):
        self.biro = None
        domain = {
            'domain': {
                'department': [
                    ('biro', '=', False)
                    ]
            }
        }
        return domain

    @api.depends('department')
    def _cek_biro(self):
        for x in self:
            if x.department:
                biro = self.env['res.branch'].search([('parent_id', '=', x.department.id)])
                if biro:
                    x.check_biro = True
                else:
                    x.check_biro = False
            else:
                x.check_biro = False

    def action_report(self):
        return self._print_report()

    def _print_report(self):
        report = self.env.ref('wika_budget_management.report_biaya_usaha').report_action(self)
        return report

    def get_budget(self):
        list_data=[]
        list_data2=[]

        grups = self.env['wika.mcs.budget.parent'].search([('parent','!=',None)],order="sequence asc")
        tanggaran = 0
        tanggaranbi = 0
        tanggaransd = 0
        tanggaranlalu = 0
        tblini = 0      # total terpakai bulan ini
        tblinip = 0     # total persen bulan ini terhadap header
        tblsd = 0       # total akumulasi terpakai bulan awal sampai bulan ini
        tbllalu = 0     # total akumulasi terpakai bulan awal sampai bulan ini
        tblsdp = 0      # total akumulasi persen bulan awal sampai bulan ini terhadap header
        tsisa = 0       # total sisa budget
        for grup in grups:
            tahun = self.tahun
            bulan = self.bulan
            list_data = []
            if self.biro:
                bulan_coa = self.env['wika.mcs.budget.coa'].search([
                    ('department', '=', self.department.id),
                    ('tahun', '=', tahun),
                    ('biro', '=', self.biro.id),
                    ('tipe_budget', '=', 'opex'),
                    ('state', '=', 'Review')],
                    order='kode_coa asc', limit=1)
                if bulan_coa:
                    if bulan < bulan_coa.bulan_review:
                        budgets = self.env['wika.mcs.budget.coa'].search([
                            ('department', '=', self.department.id),
                            ('biro', '=', self.biro.id),
                            ('tahun', '=', tahun),
                            ('tipe_budget', '=', 'opex'),
                            ('state', '=', 'Confirm')],
                            order='kode_coa asc')
                    elif bulan >= bulan_coa.bulan_review:
                        budgets = self.env['wika.mcs.budget.coa'].search([
                            ('department', '=', self.department.id),
                            ('biro', '=', self.biro.id),
                            ('tahun', '=', tahun),
                            ('tipe_budget', '=',  'opex'),
                            ('state', '=', 'Review')],
                            order='kode_coa asc')
                else:
                    budgets = self.env['wika.mcs.budget.coa'].search([
                        ('department', '=', self.department.id),
                        ('biro', '=', self.biro.id),
                        ('tahun', '=', tahun),
                        ('tipe_budget', '=',  'opex'),
                        ('state', '=', 'Confirm')],
                        order='kode_coa asc')
            elif not self.biro:
                bulan_coa = self.env['wika.mcs.budget.coa'].search([
                    ('department', '=', self.department.id),
                    ('tahun', '=', tahun),
                    ('tipe_budget', '=',  'opex'),
                    ('state', '=', 'Review')],
                    order='kode_coa asc', limit=1)
                if bulan_coa:
                    if bulan < bulan_coa.bulan_review:
                        budgets = self.env['wika.mcs.budget.coa'].search([
                            ('department', '=', self.department.id),
                            ('tahun', '=', tahun)
                            , ('tipe_budget', '=', 'opex'),
                            ('state', '=', 'Confirm')],
                            order='kode_coa asc')
                    elif bulan >= bulan_coa.bulan_review:
                        budgets = self.env['wika.mcs.budget.coa'].search([
                            ('department', '=', self.department.id),
                            ('tahun', '=', tahun),
                            ('tipe_budget', '=',  'opex'),
                            ('state', '=', 'Review')],
                            order='kode_coa asc')
                else:
                    budgets = self.env['wika.mcs.budget.coa'].search([
                        ('department', '=', self.department.id),
                        ('tahun', '=', tahun),
                        ('tipe_budget', '=',  'opex'),
                        ('state', '=', 'Confirm')],
                        order='kode_coa asc')
            else:
                raise ValidationError('Data RKAP Tidak Ditemukan')
            list_budget = []
            anggaran=0      # Total anggaran
            anggaranbi=0    # Anggaran bulan ini
            anggaransd=0    # akumulasi anggaran sd bulan ini
            anggaranlalu=0  # akumulasi anggaran sd bulan lalu
            blini=0         # terpakai bulan ini
            blinip=0        # persen bulan ini terhadap header
            blsd=0          # akumulasi terpakai bulan awal sampai bulan ini
            bllalu=0        # akumulasi terpakai bulan awal sampai bulan lalu
            blsdp=0         # akumulasi persen bulan awal sampai bulan ini terhadap header
            sisa=0          # sisa budget
            for budget in budgets:
                detail = self.env['wika.mcs.budget.bulan'].search(
                    [('coa_id', '=', budget.id),('bulan', '=', self.bulan)],limit=1)
                anggaran += budget.total_anggaran
                anggaranbi += detail.total_anggaran
                anggaransd += detail.anggaran_sd
                anggaranlalu += detail.anggaran_sd - detail.total_anggaran
                blini+= detail.terpakai_vb
                blsd+= detail.terpakai_vb_sd
                bllalu += detail.terpakai_vb_sd - detail.terpakai_vb
                sisa += budget.total_anggaran - detail.terpakai_vb_sd
                list_budget.append({
                    'ket': 'detail',
                    'uraian': '%s %s'%(budget.kode_coa.code,budget.kode_coa.name),
                    'rab': budget.total_anggaran,
                    'rabbi': detail.total_anggaran,
                    'rablalu': detail.anggaran_sd - detail.total_anggaran,
                    'rabsd': detail.anggaran_sd,
                    'blini': detail.terpakai_vb,
                    'blinip': detail.persen_hd,
                    'blsd': detail.terpakai_vb_sd,
                    'bllalu': detail.terpakai_vb_sd - detail.terpakai_vb,
                    'sisa': budget.total_anggaran - detail.terpakai_vb_sd,
                    'blsdp': detail.persen_sd,
                })
            tanggaran += anggaran
            tanggaranbi += anggaranbi
            tanggaransd += anggaransd
            tanggaranlalu += anggaranlalu
            tblini += blini
            tblsd += blsd
            tbllalu += bllalu
            tsisa += sisa
            if anggaransd>0:
                blinip = blsd/anggaransd*100
            if anggaran > 0:
                blsdp = blsd/anggaran*100
            list_data.append({
                'ket': 'grup',
                'uraian': grup.name,
                'rab': anggaran,
                'rabbi': anggaranbi,
                'rabsd': anggaransd,
                'rablalu': anggaranlalu,
                'blini': blini,
                'blinip': blinip,
                'blsd': blsd,
                'bllalu': bllalu,
                'sisa': sisa,
                'blsdp': blsdp,
            })

            list_data.extend(list_budget)
        if tanggaransd>0:
            tblinip = tblsd / tanggaransd * 100
        if tanggaran>0:
            tblsdp = tblsd / tanggaran * 100
        list_data.append({
            'ket': 'total',
            'uraian': grup.parent.name,
            'rab': tanggaran,
            'rabbi': tanggaranbi,
            'rabsd': tanggaransd,
            'rablalu': tanggaranlalu,
            'blini': tblini,
            'blinip': tblinip,
            'blsd': tblsd,
            'bllalu': tbllalu,
            'sisa': tsisa,
            'blsdp': tblsdp,
        })

        i=0
        uraian=""
        rab=0
        rabbi=0
        rabsd=0
        rablalu=0
        blini=0
        blinip=0
        blsd=0
        bllalu=0
        sisa=0
        blsdp=0
        for x in list_data:
            if x['ket']=='grup' or x['ket']=='total':
                if i!=0 and uraian !="":
                    if rabsd > 0:
                        blinip = blsd / rabsd * 100
                    if rab > 0:
                        blsdp = blsd / rab * 100
                    list_data2.append({
                        'ket': 'detail',
                        'uraian': uraian,
                        'rab': rab,
                        'rabbi': rabbi,
                        'rabsd': rabsd,
                        'rablalu': rablalu,
                        'blini': blini,
                        'blinip': blinip,
                        'blsd': blsd,
                        'bllalu': bllalu,
                        'sisa': sisa,
                        'blsdp': blsdp,
                    })
                    i=0
                list_data2.append({
                    'ket': x['ket'],
                    'uraian': x['uraian'],
                    'rab': x['rab'],
                    'rabbi': x['rabbi'],
                    'rabsd': x['rabsd'],
                    'rablalu': x['rablalu'],
                    'blini': x['blini'],
                    'blinip': x['blinip'],
                    'blsd': x['blsd'],
                    'bllalu': x['bllalu'],
                    'sisa': x['sisa'],
                    'blsdp': x['blsdp'],
                })

            else:
                if x['uraian']== uraian:
                    rab+=x['rab']
                    rabbi+=x['rabbi']
                    rabsd+=x['rabsd']
                    rablalu+=x['rablalu']
                    blini+=x['blini']
                    blsd+=x['blsd']
                    bllalu+=x['bllalu']
                    sisa+=x['sisa']
                else:
                    if i!=0:
                        if rabsd>0:
                            blinip=blsd/rabsd*100
                        if rab>0:
                            blsdp=blsd/rab*100
                        list_data2.append({
                            'ket': 'detail',
                            'uraian': uraian,
                            'rab': rab,
                            'rabbi': rabbi,
                            'rabsd': rabsd,
                            'rablalu': rablalu,
                            'blini': blini,
                            'blinip': blinip,
                            'blsd': blsd,
                            'bllalu': bllalu,
                            'sisa': sisa,
                            'blsdp': blsdp,
                        })
                        uraian = x['uraian']
                        rab = x['rab']
                        rabbi = x['rabbi']
                        rabsd = x['rabsd']
                        rablalu = x['rablalu']
                        blini = x['blini']
                        blsd = x['blsd']
                        bllalu = x['bllalu']
                        sisa = x['sisa']

            if x['ket'] == 'detail' and i == 0:
                uraian = x['uraian']
                rab = x['rab']
                rabbi = x['rabbi']
                rabsd = x['rabsd']
                rablalu = x['rablalu']
                blini = x['blini']
                blsd = x['blsd']
                bllalu = x['bllalu']
                sisa = x['sisa']
                i += 1
        return list_data2

class WikaTipeBudget(models.Model):
    _name = 'wika.tipe.budget'
    _description ='Tipe Budgeting'

    code = fields.Char(string='Kode Budget', required=True, copy=False)
    name= fields.Char(string='Tipe Budget',required=True,copy=False)
