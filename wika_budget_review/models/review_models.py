from odoo import fields, api, models,_
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime
import pytz
from pytz import timezone

def get_years():
    year_list = []
    for i in range(2020, 2100):
        year_list.append((str(i), str(i)))
    return year_list

class WikaMCSBudgetReview(models.Model):
    _name = 'wika.mcs.budget.review'
    _description = 'Budget Review'

    @api.model
    def _get_default_branch(self):
        user = self.env.user
        branch_id = user.branch_id
        if branch_id:
            if branch_id.biro:
                return branch_id.parent_id.id
            else:
                return branch_id.id
        return False

    bulan = fields.Selection([('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'),
                              ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'),
                              ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember'), ],
                             string='Month', default='9')
    tahun = fields.Selection(get_years(), string='Year')
    department = fields.Many2one(comodel_name='res.branch', string='Divisi',copy=False,default=_get_default_branch)
    persentase = fields.Float(string='Persentase Kenaikan')
    type = fields.Selection([('review', 'Review'), ('rkap', 'RKAP')], string='Type', default='review')
    persentase_turun = fields.Float(string='Persentase Penurunan')
    review_ids = fields.One2many('wika.mcs.budget.review.line', 'review_id', ondelete='cascade', string='Per Bulan', index=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('reviewed', 'Reviewed'),
        ('rkap', 'RKAP Created')
    ], string='State', default='draft')
    status_generate = fields.Boolean(string="Status Generate", copy=False, default=False)
    check_biro = fields.Boolean(compute="_cek_biro")
    biro = fields.Many2one(comodel_name='res.branch', string='Department')

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

    @api.onchange('tahun','bulan','department','biro','persentase_turun','persentase')
    def _onchange_header(self):
        if self.department and self.persentase_turun>0.0:
            template_line = []
            budgets = None
            if self.check_biro == False:
                budgets = self.env['wika.mcs.budget.coa'].search(
                    [('department', '=', self.department.id),('tahun', '=', self.tahun),('state','=','Confirm'),('tipe_budget','=','opex')])
            else:
                if self.biro:
                    budgets = self.env['wika.mcs.budget.coa'].search(
                        [('department', '=', self.department.id),('biro', '=', self.biro.id),
                         ('tahun', '=', self.tahun),('state','=','Confirm'),('tipe_budget','=','opex')])
            if budgets:
                for budget in budgets:
                    template_line.append([0, 0, {
                        'review_id': self.id,
                        'budget_id': budget.id,
                        'kode_perkiraan_id':budget.kode_coa.id,
                        'rkap':budget.total_anggaran,
                        'rkap_review': budget.total_anggaran - (self.persentase_turun / 100 * budget.total_anggaran)
                    }])

            self.review_ids = template_line
        if self.department and self.persentase>0.0:
            template_line = []
            budgets = None
            if self.check_biro == False:
                budgets = self.env['wika.mcs.budget.coa'].search([
                    ('department', '=', self.department.id),
                    ('tahun', '=', self.tahun-1),
                    ('state', '=', 'Review'),
                    ('tipe_budget', '=', 'opex')
                ])
                if not budgets: 
                    budgets = self.env['wika.mcs.budget.coa'].search([
                        ('department', '=', self.department.id),
                        ('tahun', '=', self.tahun-1),
                        ('state','=','Confirm'),
                        ('tipe_budget','=','opex')
                    ])
            else:
                if self.biro:
                    budgets = self.env['wika.mcs.budget.coa'].search([
                        ('department', '=', self.department.id),
                        ('biro', '=', self.biro.id),
                        ('tahun', '=', self.tahun-1),
                        ('state', '=', 'Review'),
                        ('tipe_budget', '=', 'opex')
                    ])
                    if not budgets: 
                        budgets = self.env['wika.mcs.budget.coa'].search([
                            ('department', '=', self.department.id),
                            ('biro', '=', self.biro.id),
                            ('tahun', '=', self.tahun-1),
                            ('state', '=', 'Confirm'),
                            ('tipe_budget', '=', 'opex')
                        ])

            if budgets:
                for budget in budgets:
                    template_line.append([0, 0, {
                        'review_id': self.id,
                        'budget_id': budget.id,
                        'kode_perkiraan_id': budget.kode_coa.id,
                        'rkap': budget.total_anggaran,
                        'rkap_review': budget.total_anggaran + (self.persentase / 100 * budget.total_anggaran)
                    }])
            self.review_ids = template_line

    def act_draft(self):
        self.state = 'confirm'

    def act_confirm(self):
        if self.type =='review':
            if self.biro:
                budget = self.env['wika.mcs.budget.coa'].search([
                    ('department','=',self.department.id),
                    ('tahun','=',self.tahun),
                    ('biro','=',self.biro.id),
                    ('state', '=', 'Review'),
                    ('tipe_budget','=','opex')
                ])
            else:
                budget = self.env['wika.mcs.budget.coa'].search([
                    ('department', '=', self.department.id),
                    ('tahun', '=', self.tahun),
                    ('state', '=', 'Review'),
                    ('tipe_budget','=','opex')
                ])

            if budget:
                for x in budget:
                    del_budget = f"""DELETE FROM wika_mcs_budget_coa WHERE id = {x.id}"""
                    self._cr.execute(del_budget)
            
            for x in self.review_ids:
                spl = x.kode_perkiraan.code[0:4]
                grup = self.env['wika.mcs.budget.parent'].search([('name','ilike',spl)],limit=1)
                budget_id = self.env['wika.mcs.budget.coa'].create({
                    'tahun': self.tahun,
                    'tipe_budget': 'opex',
                    'department': self.department.id,
                    'biro': self.biro.id or None,
                    'kode_coa': x.kode_perkiraan.id,
                    'state': 'Review',
                    'grup_akun': grup.id,
                    'bulan_review': self.bulan
                })
                for product in x.detail_ids:
                    product_id = self.env['wika.mcs.budget.coa.detail'].create({
                        'coa_id': budget_id.id,
                        'pekerjaan': product.product_id.id,
                        'vol': product.vol,
                        'satuan' : product.satuan,
                        'harga_satuan':product.harga_satuan,
                        'anggaran': product.anggaran,
                        'is_beban':product.is_beban,
                        'beban':product.beban,
                        'total_anggaran':product.total_anggaran,
                        'total_beban':product.total_beban,
                        'status_generate':True
                    })

                    for bulan in product.line_ids:
                        bulan = self.env['wika.mcs.budget.coa.detail.line'].create({
                            'detail_id':product_id.id,
                            'bulan':bulan.bulan,
                            'anggaran':bulan.prognosa,
                            'sequence': bulan.bulan
                        })

                    for beban in product.beban_ids:
                        beban = self.env['wika.mcs.budget.coa.detail.beban'].create({
                            'detail_id':product_id.id,
                            'branch_id': beban.branch_id.id,
                            'persen':beban.persen,
                            'anggaran':beban.anggaran,
                        })

                budget_id.act_generate()
            result = self.state = 'reviewed'

        if self.type =='rkap':
            if self.biro:
                budget = self.env['wika.mcs.budget.coa'].search([
                    ('department', '=', self.department.id),
                    ('tahun','=', self.tahun-1),
                    ('biro', '=', self.biro.id),
                    ('state', '=', 'Review'),
                    ('tipe_budget', '=', 'opex')
                ])
                if not budget:
                    budget = self.env['wika.mcs.budget.coa'].search([
                        ('department','=',self.department.id),
                        ('tahun', '=', self.tahun-1),
                        ('biro', '=', self.biro.id),
                        ('state', '=', 'Confirm'),
                        ('tipe_budget', '=', 'opex')
                    ])
            if not self.biro:
                budget = self.env['wika.mcs.budget.coa'].search([
                    ('department', '=', self.department.id),
                    ('tahun', '=', self.tahun-1),
                    ('state', '=', 'Confirm'),
                    ('tipe_budget','=','opex')
                ])
                if not budget:
                    budget = self.env['wika.mcs.budget.coa'].search([
                        ('department', '=', self.department.id),
                        ('tahun', '=', self.tahun-1),
                        ('state', '=', 'Review'),
                        ('tipe_budget','=','opex')
                    ])

            for x in self.review_ids:
                spl = x.kode_perkiraan_id.code[0:4]
                grup = self.env['wika.mcs.budget.parent'].search([('name','ilike',spl)],limit=1)
                budget_id = self.env['wika.mcs.budget.coa'].create({
                                'tahun': self.tahun,
                                'tipe_budget':'opex',
                                'department': self.department.id,
                                'biro': self.biro.id or None,
                                'kode_coa': x.kode_perkiraan_id.id,
                                'state': 'Confirm',
                                'grup_akun': grup.id                     
                            })
                for product in x.detail_ids:
                    product_id = self.env['wika.mcs.budget.coa.detail'].create({
                        'coa_id': budget_id.id,
                        'pekerjaan': product.product_id.id,
                        'vol': product.vol,
                        'satuan' : product.satuan,
                        'harga_satuan':product.harga_satuan,
                        'anggaran': product.anggaran,
                        'is_beban':product.is_beban,
                        'beban':product.beban,
                        'total_anggaran':product.total_anggaran,
                        'total_beban':product.total_beban,
                        'status_generate':True
                    })
                    total_prognosa = 0.0
                    for bulan in product.line_ids:
                        bulan = self.env['wika.mcs.budget.coa.detail.line'].create({
                            'detail_id': product_id.id,
                            'bulan': bulan.bulan,
                            'anggaran': bulan.nilai_rkap,
                            'sequence': bulan.bulan
                        })

                        if x.budget_id.id:
                            update_budget = """UPDATE wika_mcs_budget_bulan 
                            SET prognosa = (
                                SELECT
                                    SUM(data.prognosa)
                                FROM
                                    wika_mcs_budget_review_line_prognosa data
                                LEFT JOIN
                                    wika_review_line_detail line on line.id=data.review_id
                                LEFT JOIN
                                    wika_mcs_budget_review_line rev on rev.id = line.line_id
                                LEFT JOIN
                                    wika_mcs_budget_coa budget on budget.id=rev.budget_id
                                WHERE
                                    budget.id = %s and data.bulan = %s
                                GROUP BY
                                    budget.id)
                                WHERE
                                    coa_id = %s AND bulan =%s
                            """ % (x.budget_id.id, bulan.bulan, x.budget_id.id, bulan.bulan)
                            self._cr.execute(update_budget)
                    
                    for beban in product.beban_ids:
                        beban = self.env['wika.mcs.budget.coa.detail.beban'].create({
                            'detail_id': product_id.id,
                            'branch_id': beban.branch_id.id,
                            'persen': beban.persen,
                            'anggaran': beban.anggaran,
                        })
                budget_id.act_generate()
            
            result = self.state = 'rkap'
        return result

    @api.depends('type')
    def act_generate(self):
        if self.status_generate == False and self.type == 'review':
            if self.review_ids:
                for x in self.review_ids:
                    if x.budget_id:
                        for data in x.budget_id.detail_ids:
                            product_id = self.env['wika.review.line.detail'].create({
                                'line_id': x.id,
                                'budget_detail_id': data.id,
                                'product_id': data.pekerjaan.id,
                                'vol': data.vol,
                                'satuan': data.satuan,
                                'harga_satuan': data.harga_satuan,
                                'anggaran': data.anggaran,
                                'is_beban': data.is_beban,
                                'beban': data.beban,
                                'total_anggaran': data.total_anggaran,
                                'total_beban': data.total_beban,
                                'total_rencana': data.vol * data.harga_satuan,
                                'status_generate': True
                            })

                            for bln in data.line_ids:
                                if self.biro:
                                    query = """
                                        SELECT
                                            SUM(invl.price_subtotal)            
                                        FROM
                                            account_move_line invl                            
                                        LEFT JOIN
                                            account_move inv ON inv.id = invl.move_id
                                        LEFT JOIN
                                            account_account coa ON coa.id = invl.account_id
                                        LEFT JOIN
                                            product_product product ON product.id = invl.product_id
                                        WHERE
                                            TO_CHAR(inv.date,'yyyy')= '%s' AND
                                            TO_CHAR(inv.date,'fmMM') ='%s' AND
                                            inv.biro = %s and inv.branch_id = %s AND
                                            invl.account_id = %s AND
                                            invl.product_id = %s  
                                    """ % (self.tahun, bln.bulan, self.biro.id, self.department.id, x.kode_perkiraan.id, product_id.product_id.id)

                                elif not self.biro:
                                    query = """
                                         SELECT
                                           SUM(invl.price_subtotal)
                                         FROM
                                            account_move_line invl
                                         LEFT JOIN
                                            account_move inv on inv.id = invl.move_id
                                         LEFT JOIN
                                            account_account coa on coa.id = invl.account_id
                                         LEFT JOIN
                                            product_product product on product.id = invl.product_id
                                         WHERE
                                            TO_CHAR(inv.date, 'yyyy') = '%s' AND
                                            TO_CHAR(inv.date,'fmMM') = '%s' AND
                                            inv.branch_id = %s AND
                                            invl.account_id = %s AND
                                            invl.product_id = %s
                                   """ % (self.tahun, bln.bulan,self.department.id, x.kode_perkiraan.id, product_id.product_id.id)
                                    
                                self._cr.execute(query)
                                hasil = 0.0
                                hasil = self._cr.fetchone()[0]
                                self.env['wika.mcs.budget.review.line.prognosa'].create({
                                    'review_id': product_id.id,
                                    'bulan': bln.bulan,
                                    'rencana': bln.anggaran,
                                    'realisasi': hasil,
                                    'prognosa': bln.anggaran,
                                    })
    
                            for beban in data.beban_ids:
                                self.env['wika.review.beban'].create({
                                    'detail_id': product_id.id,
                                    'detil_beban_id': beban.id,
                                    'total_rencana':product_id.total_rencana,
                                    'branch_id': beban.branch_id.id,
                                    'persen': beban.persen,
                                    'anggaran': beban.anggaran
                                })
                self.status_generate = True

        if self.status_generate == False and self.type == 'rkap':
            if self.review_ids:
                for x in self.review_ids:
                    if x.budget_id:
                        for data in x.budget_id.detail_ids:
                            product_id = self.env['wika.review.line.detail'].create({
                                'line_id': x.id,
                                'budget_detail_id': data.id,
                                'product_id': data.pekerjaan.id,
                                'vol': data.vol,
                                'satuan': data.satuan,
                                'harga_satuan': data.harga_satuan,
                                'anggaran': data.anggaran,
                                'is_beban': data.is_beban,
                                'beban': data.beban,
                                'total_anggaran': data.total_anggaran,
                                'total_beban': data.total_beban,
                                'total_rencana': data.vol * data.harga_satuan,
                                'status_generate': True
                            })

                            print(product_id)
                            for bln in data.line_ids:
                                if self.biro:
                                    query = """
                                        SELECT
                                            SUM(invl.price_subtotal)            
                                        FROM
                                            account_move_line invl                            
                                        LEFT JOIN
                                            account_move inv ON inv.id = invl.move_id
                                        LEFT JOIN
                                            account_account coa ON coa.id = invl.account_id
                                        LEFT JOIN
                                            product_product product ON product.id = invl.product_id
                                        WHERE
                                            TO_CHAR(inv.date,'yyyy') = '%s' AND
                                            TO_CHAR(inv.date,'fmMM') = '%s' AND
                                            inv.biro = %s AND
                                            inv.branch_id = %s AND
                                            invl.account_id= %s AND
                                            invl.product_id = %s  
                                    """ % (self.tahun-1, bln.bulan, self.biro.id, self.department.id, x.kode_perkiraan.id, product_id.product_id.id)
                                elif not self.biro:
                                    query = """
                                        SELECT
                                            SUM(invl.price_subtotal)
                                        FROM
                                            account_move_line invl
                                        LEFT JOIN
                                            account_move inv ON inv.id = invl.move_id
                                        LEFT JOIN
                                            account_account coa ON coa.id = invl.account_id
                                        LEFT JOIN
                                            product_product product ON product.id = invl.product_id
                                        WHERE
                                            TO_CHAR(inv.date, 'yyyy') = '%s' AND
                                            TO_CHAR(inv.date,'fmMM') = '%s' AND
                                            inv.branch_id = %s and
                                            invl.account_id = %s and
                                            invl.product_id = %s
                                        """% (self.tahun-1, bln.bulan,self.department.id, x.kode_perkiraan.id, product_id.product_id.id)
                                    
                                self._cr.execute(query)
                                hasil = 0.0
                                hasil = self._cr.fetchone()[0]
                                self.env['wika.mcs.budget.review.line.prognosa'].create({
                                    'review_id': product_id.id,
                                    'bulan': bln.bulan,
                                    'rencana': bln.anggaran,
                                    'realisasi': hasil,
                                    'prognosa': bln.anggaran,
                                    'nilai_rkap': bln.anggaran,
                                    })
                            for beban in data.beban_ids:
                                print(beban)
                                self.env['wika.review.beban'].create({
                                    'detail_id': product_id.id,
                                    'detil_beban_id': beban.id,
                                    'total_rencana':product_id.total_rencana,
                                    'branch_id': beban.branch_id.id,
                                    'persen': beban.persen,
                                    'anggaran': beban.anggaran
                                })
                self.status_generate = True

    def name_get(self):
        res = []
        for record in self:
            biro = ""
            if record.biro:
                biro = " - %s" % record.biro.code
            tit = "[%s] [%s%s] - Review" % (
            record.tahun, record.department.code, biro)
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

class WikaReviewLineDetail(models.Model):
    _name = 'wika.review.line.detail'
    _rec_name = 'product_id'

    line_id = fields.Many2one(comodel_name='wika.mcs.budget.review.line', string='ID Review', ondelete='cascade')
    budget_detail_id = fields.Many2one(comodel_name='wika.mcs.budget.coa.detail', string='ID Budget Line')
    product_id = fields.Many2one(string='Nama Pekerjaan', comodel_name='product.product')
    vol = fields.Float(string='Volume')
    satuan = fields.Char(string='Satuan')
    harga_satuan = fields.Float(string='Harga Satuan')
    anggaran = fields.Float(string='Anggaran',compute='compute_anggaran',store=True)
    is_beban = fields.Boolean(string="Dibebankan")
    beban = fields.Float(string="Beban (%)")
    total_anggaran = fields.Float(string='Total Anggaran',compute='_compute_total_anggaran', store=True)
    total_beban = fields.Float(string='Total Beban', compute='_compute_total_beban', store=True)
    total_rencana = fields.Float(string='Total Rencana Anggaran',compute='_compute_total_rencana', store=True)

    line_ids = fields.One2many(string="Bulan", comodel_name='wika.mcs.budget.review.line.prognosa',
                               inverse_name='review_id',
                               index=True, ondelete='cascade', copy=True)
    beban_ids = fields.One2many(string="Beban", comodel_name='wika.review.beban',
                               inverse_name='detail_id',
                               index=True, ondelete='cascade', copy=True)
    status_generate = fields.Boolean(string="Status Generate", copy=False, default=False)
    total_bulan = fields.Integer(compute='_compute_total_bulan')
                
    @api.depends('beban_ids.anggaran')
    def compute_anggaran_beban(self):
        for bbn in self.beban_ids:
            if bbn.persen:
                bbn.anggaran = bbn.total_rencana * bbn.persen / 100

    @api.depends('beban_ids.anggaran')
    def _compute_total_beban(self):
        for x in self:
            x.total_beban = sum(z.anggaran for z in x.beban_ids)

    @api.depends('vol','harga_satuan')
    def _compute_total_rencana(self):
        for x in self:
            x.total_rencana = x.vol * x.harga_satuan

    @api.depends('vol','harga_satuan','beban')
    def compute_anggaran(self):
        for x in self:
            if x.beban > 0.0:
                x.anggaran = (x.beban/100) * x.harga_satuan * x.vol
            else:
                x.anggaran = x.vol*x.harga_satuan

    @api.depends('line_ids.prognosa','line_id.review_id.type')
    def _compute_total_anggaran(self):
        for x in self:
            if x.line_id.review_id.type == 'review':
                x.total_anggaran = sum(z.prognosa for z in x.line_ids)
            if x.line_id.review_id.type == 'rkap':
                x.total_anggaran = sum(z.nilai_rkap for z in x.line_ids)

    def act_bulan(self):
        if self.line_id.review_id.type == 'review':
            form_id = self.env.ref('wika_budget_review.review_line_detail_form_view')
            ctx = {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true', 'default_id': self.id}
        else:
            form_id = self.env.ref('wika_budget_review.review_line_detail_form_view')
            # form_id = self.env.ref('wika_budget_generate_rkap.generate_rkap_review_line_detail_form_view')
            ctx = {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true', 'default_id': self.id}
        return {
            'name': 'Per Bulan',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wika.review.line.detail',
            'view_id': form_id.id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'current',
            'context': ctx
        }

    def act_beban(self):
        if self.line_id.review_id.type == 'review':
            form_id = self.env.ref('wika_budget_review.review_line_detail_form_beban_view')
            ctx = {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true', 'default_id': self.id}
        else:
            # form_id = self.env.ref('wika_budget_generate_rkap.generate_rkap_review_line_detail_form_beban_view')
            form_id = self.env.ref('wika_budget_review.review_line_detail_form_beban_view')
            ctx = {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true', 'default_id': self.id}

        return {
            'name': 'Pembebanan',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wika.review.line.detail',
            'view_id': form_id.id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'current',
            'context': ctx
        }

class WikaMCSBudgetReviewLinePrognosa(models.Model):
    _name = 'wika.mcs.budget.review.line.prognosa'

    review_id = fields.Many2one(comodel_name='wika.review.line.detail', string='ID Review', ondelete='cascade')
    realisasi = fields.Float('Realisasi s/d Bulan Dipilih',related='review_id.line_id.realisasi')
    bulan_review = fields.Selection([('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'),
                              ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'),
                              ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember'), ],
                             string='Bulan Review',related='review_id.line_id.review_id.bulan')
    bulan = fields.Selection([('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'),
                              ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'),
                              ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember'), ],
                             string='Bulan')
    rencana = fields.Float('Rencana')
    realisasi = fields.Float('Realisasi')
    prognosa = fields.Float('Prognosa')
    nilai_rkap = fields.Float('RKAP Tahun Berikutnya')
    sequence = fields.Integer(string='Sequence')

class WikaReviewBeban(models.Model):
    _name = 'wika.review.beban'
    _description = 'Review Beban'

    detail_id = fields.Many2one(string="ID Detail", ondelete='cascade', comodel_name='wika.review.line.detail', index=True)
    budget_id = fields.Many2one(comodel_name='wika.mcs.budget.coa', related='detail_id.line_id.budget_id',store=True)
    detil_beban_id = fields.Many2one(comodel_name='wika.mcs.budget.coa.detail.beban')
    total_rencana = fields.Float(related='detail_id.total_rencana')
    branch_id = fields.Many2one(string="Divisi", comodel_name='res.branch', index=True)
    persen = fields.Float(string='Persen')
    anggaran = fields.Float(string='Anggaran', index=True)

    @api.onchange('persen')
    def _onchange_persen(self):
        self.anggaran = self.total_rencana * self.persen / 100

    @api.onchange('anggaran')
    def _onchange_anggaran(self):
        self.persen = self.anggaran / self.total_rencana * 100

class WikaMCSBudgetReviewLine(models.Model):
    _name = 'wika.mcs.budget.review.line'
    _rec_name = 'kode_perkiraan_id'

    review_id = fields.Many2one(comodel_name='wika.mcs.budget.review', string='ID Review', ondelete='cascade')
    budget_id = fields.Many2one(string='Budget', comodel_name='wika.mcs.budget.coa')
    persentase = fields.Float(string='Persentase Kenaikan', related='review_id.persentase',store=True)
    persentase_turun = fields.Float(string='Persentase Penurunan', related='review_id.persentase_turun',store=True)
    kode_perkiraan = fields.Many2one(string="Kode Perkiraan", comodel_name='account.account',related='budget_id.kode_coa')
    kode_perkiraan_id = fields.Many2one(string="Kode Perkiraan", comodel_name='account.account')
    rkap = fields.Float( string='RKAP',related='budget_id.total_anggaran')
    rkap_review = fields.Float(string='Simulasi Penurunan RKAP', compute='change_rkap_review')
    realisasi = fields.Float('Realisasi s/d Bulan Dipilih', compute='_compute_ripersen')
    realisasi_persen = fields.Float('% ri Thd RKAP', compute='_compute_ripersen')
    sisa_anggaran = fields.Float('Sisa Anggaran (s/d bulan Dipilih)', compute='_compute_sisa')
    prognosa = fields.Float('Sisa Biaya s/d Desember', compute='_compute_prognosa')
    prognosa_sd = fields.Float('RKAP Review', compute='_compute_rkap_review')
    rkap_ts = fields.Float(string='RKAP Tahun Selanjutnya', compute='_compute_rkap_ts')

    ts_persen = fields.Float('% RKAP Tahun Selanjutnya vs Prognosa', compute="_compute_tspersen")
    ts_persen_rkap = fields.Float('% RKAP Tahun Selanjutnya vs RKAP Awal', compute="_compute_tspersen")
    selisih = fields.Float('Selisih Tahun Selanjutnya - Prognosa', compute="_compute_selisih")

    detail_ids = fields.One2many(string='Product Detail', comodel_name='wika.review.line.detail', ondelete='cascade',
                                 inverse_name='line_id', index=True)
    status_generate =fields.Boolean(string="Status Generate", copy=False, default=False,related='review_id.status_generate',store=True)

    def act_generate(self):
        for x in self.detail_ids:
            if x.status_generate==False:
                for i in range(12):
                    bulan = str(i+1)
                    self.env['wika.mcs.budget.review.line.prognosa'].create({
                        'review_id': x.id,
                        'bulan': bulan,
                        'sequence': i+1,
                        'rencana': 0,
                        'realisasi': 0,
                        'prognosa': 0,
                    })
                x.status_generate = True
            
    @api.depends('rkap','review_id.type','detail_ids.line_ids.prognosa')
    def _compute_prognosa(self):
        for x in self:
            if x.rkap > 0 and x.review_id.type=='review':
                prog=0.0
                line = self.env['wika.mcs.budget.bulan'].search([('bulan', '>', x.review_id.bulan), ('coa_id', '=', x.budget_id.id)])
                for data in line:
                    prog += data.total_anggaran
                x.prognosa = prog

            elif x.review_id.type=='rkap' :
                prog=0.0
                for y in x.detail_ids:
                    if y.line_ids:
                        prog+=sum(z.prognosa for z in y.line_ids)
                x.prognosa = prog
             
            else:
                x.prognosa=0.0

    @api.depends('detail_ids.total_anggaran','review_id.type')
    def _compute_rkap_review(self):
        
        for x in self:
            if x.detail_ids and x.review_id.type == 'review':
                x.prognosa_sd = sum(z.total_anggaran for z in x.detail_ids)
            else:
                x.prognosa_sd = 0.0


    @api.depends('rkap','review_id')
    def _compute_sisa(self):
        for x in self:
            if x.rkap > 0 and x.review_id.type=='review':
                terpakai = 0.0
                line = self.env['wika.mcs.budget.bulan'].search([('bulan', '=', x.review_id.bulan), ('coa_id', '=', x.budget_id.id)],limit=1)
                terpakai = line.terpakai_vb_sd
                x.sisa_anggaran = x.rkap - terpakai
            elif x.review_id.type=='rkap':
                terpakai = 0.0
                line = self.env['wika.mcs.budget.bulan'].search([('bulan', '=', 12), ('coa_id', '=', x.budget_id.id)],limit=1)
                terpakai = line.terpakai_vb_sd
                x.sisa_anggaran = x.prognosa - x.realisasi
            else:
                x.sisa_anggaran=0.0


    @api.depends('rkap','review_id.type')
    def _compute_ripersen(self):
        for x in self:

            if x.rkap > 0 and x.review_id.biro:
                hasil = 0.0
                if x.review_id.type == 'review':
                    tahun = str(x.review_id.tahun)
                if x.review_id.type == 'rkap':
                    tahun = str(x.review_id.tahun-1)
                bulan = str(x.review_id.bulan)
                dept = x.review_id.biro.id
                div = x.review_id.department.id
                query = """
                        SELECT
                            SUM(invl.price_subtotal)
                        FROM
                            account_move_line invl
                        LEFT JOIN
                            account_move inv ON inv.id = invl.move_id
                        LEFT JOIN
                            account_account coa ON coa.id = invl.account_id
                        WHERE
                            TO_CHAR(inv.date,'yyyy') = '%s' AND
                            TO_CHAR(inv.date,'fmMM') <= '%s' AND
                            inv.biro = %s AND
                            inv.branch_id = %s AND 
                            (invl.account_id = %s::integer OR invl.account_id IS NULL)
                        """%(tahun,bulan,dept,div,x.kode_perkiraan.id)
                self._cr.execute(query)
                hasil =self._cr.fetchone()[0]
                x.realisasi = hasil

                x.realisasi_persen = x.realisasi / x.rkap * 100
                #x.prognosa_sd = x.realisasi + x.prognosa
            elif x.rkap > 0 and not x.review_id.biro:
                terpakai = 0.0
                line = self.env['wika.mcs.budget.bulan'].search([('bulan', '=', x.review_id.bulan), ('coa_id', '=', x.budget_id.id)],limit=1)
                terpakai = line.terpakai_vb_sd
                x.realisasi = terpakai
                x.realisasi_persen = x.realisasi/x.rkap * 100
            else:
                x.realisasi_persen = 0.0
                x.realisasi = 0.0

    @api.depends('review_id.type','detail_ids.total_anggaran')
    def _compute_rkap_ts(self):
        for x in self:
            if x.detail_ids and x.review_id.type == 'rkap':
                x.rkap_ts = sum(z.total_anggaran for z in x.detail_ids)
            else:
                x.rkap_ts = 0.0

    @api.depends('rkap_ts', 'rkap')
    def _compute_tspersen(self):
        for x in self:
            x.ts_persen_rkap = 0.0
            if x.rkap_ts > 0:
                x.ts_persen = x.prognosa / x.rkap_ts * 100
                x.ts_persen_rkap = x.rkap / x.rkap_ts * 100
            else:
                x.ts_persen = 0.0
                x.ts_persen_rkap = 0.0

    @api.depends('review_id.persentase_turun','rkap','review_id.persentase','budget_id')
    def change_rkap_review(self):
        for x in self:
            if x.review_id.persentase_turun>0.0:
                if x.review_id.biro:
                    rkap = self.env['wika.mcs.budget.coa'].search(
                        [('kode_coa','=',x.kode_perkiraan.id),('department','=',x.review_id.department.id),
                        ('biro','=',x.review_id.biro.id),('tahun','=',x.review_id.tahun),('state', '=', 'Confirm'),('tipe_budget','=','opex')])
                elif not x.review_id.biro:
                    rkap = self.env['wika.mcs.budget.coa'].search(
                        [('kode_coa', '=', x.kode_perkiraan.id), ('department', '=', x.review_id.department.id),
                        ('tahun', '=', x.review_id.tahun), ('state', '=', 'Confirm'),('tipe_budget','=','opex')])
                x.rkap_review = rkap.total_anggaran - (x.persentase_turun/100*rkap.total_anggaran)
            else:
                x.rkap_review = 0.0

            if x.review_id.persentase>0.0:
                x.rkap_review = x.budget_id.total_anggaran + (x.persentase/100*x.budget_id.total_anggaran)
            else:
                x.rkap_review = 0.0

    @api.onchange('rkap')
    def change_rkap(self):
        for x in self:
            if x.rkap > 0:
                x.rkap_review = x.rkap + (x.review_id.persentase/100*x.rkap)

    @api.depends('rkap_ts', 'prognosa')
    def _compute_selisih(self):
        for x in self:
            x.selisih = x.rkap_ts - x.prognosa

    def act_detail_pekerjaan(self):
        if self.review_id.state == 'reviewed' and self.review_id.type=='review':
            form_id = self.env.ref('wika_budget_review.review_form_view_2_2')
            ctx = {}
        elif self.review_id.state not in ('reviewed','rkap') and self.review_id.type=='review':
            form_id = self.env.ref('wika_budget_review.review_form_view_2')
            ctx = {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true', 'default_id': self.id}
        elif self.review_id.state == 'rkap' and self.review_id.type=='rkap':
            form_id = self.env.ref('wika_budget_review.review_form_view_2')
            ctx = {}
        elif self.review_id.state not in ('reviewed','rkap')  and self.review_id.type=='rkap':
            form_id = self.env.ref('wika_budget_review.generate_rkap_line_form_view_2')
            ctx = {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true', 'default_id': self.id}

        return {
            'name': 'Detail Pekerjaan',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wika.mcs.budget.review.line',
            'view_id': form_id.id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'current',
            'context': ctx
        }
