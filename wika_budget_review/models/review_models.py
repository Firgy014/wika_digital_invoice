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
        user_obj = self.env['res.users']
        branch_id = user_obj.browse(self.env.user.id).branch_id or False
        if branch_id.biro == True:
            branch_id = branch_id.parent_id.id
        else:
            branch_id = branch_id.id
        return branch_id

    bulan = fields.Selection([('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'), ('4', 'April'),
                              ('5', 'Mei'), ('6', 'Juni'), ('7', 'Juli'), ('8', 'Agustus'),
                              ('9', 'September'), ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember'), ],
                             string='Month', default='9')
    tahun = fields.Selection(get_years(), string='Year')
    department = fields.Many2one(comodel_name='res.branch', string='Divisi',copy=False,default=_get_default_branch)
    persentase = fields.Float(string='Persentase Kenaikan')
    type = fields.Selection([('review', 'review'), ('rkap', 'RKAP')], string='Type')
    persentase_turun = fields.Float(string='Persentase Penurunan')
    # review_ids = fields.One2many(string='Per Bulan', comodel_name='wika.mcs.budget.review.line', ondelete='cascade',
    #                              inverse_name='review_id', index=True)
    # state       = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('reviewed', 'Reviewed'), ('rkap', 'RKAP Created')],
    #                          'State', default='draft')
    # status_generate=fields.Boolean(string="Status Generate", copy=False, default=False)
    # check_biro = fields.Boolean(compute="_cek_biro")
    # biro = fields.Many2one(comodel_name='res.branch', string='Department')

    # @api.depends('department')
    # def _cek_biro(self):
    #     for x in self:
    #         if x.department:
    #             biro = self.env['res.branch'].search([('parent_id', '=', x.department.id)])
    #             if biro:
    #                 x.check_biro = True
    #             else:
    #                 x.check_biro = False
    #         else:
    #             x.check_biro = False


    # @api.onchange('tahun','bulan','department','biro','persentase_turun','persentase')
    # def _onchange_header(self):
    #     if self.department and self.persentase_turun>0.0:
    #         template_line = []
    #         budgets=None
    #         if self.check_biro==False:
    #             budgets = self.env['mcs.budget.coa'].search(
    #                 [('department', '=', self.department.id), ('tahun', '=', self.tahun),('state','=','Confirm'),('tipe_budget','=','opex')])
    #         else:
    #             if self.biro:
    #                 budgets = self.env['mcs.budget.coa'].search(
    #                     [('department', '=', self.department.id),('biro', '=', self.biro.id),
    #                      ('tahun', '=', self.tahun),('state','=','Confirm'),('tipe_budget','=','opex')])
    #         if budgets:
    #             for budget in budgets:
    #                 template_line.append([0, 0, {
    #                     'review_id': self.id,
    #                     'budget_id': budget.id,
    #                     'kode_perkiraan_id':budget.kode_coa.id,
    #                     'rkap':budget.total_anggaran,
    #                     'rkap_review': budget.total_anggaran - (self.persentase_turun / 100 * budget.total_anggaran)
    #                 }])
    #         self.review_ids=template_line
    #     if self.department and self.persentase>0.0:
    #         template_line = []
    #         budgets=None
    #         if self.check_biro==False:
    #             budgets = self.env['mcs.budget.coa'].search(
    #                 [('department', '=', self.department.id), ('tahun', '=', self.tahun-1),('state','=','Review'),('tipe_budget','=','opex')])
    #             if not budgets: 
          
    #                 budgets = self.env['mcs.budget.coa'].search(
    #                 [('department', '=', self.department.id), ('tahun', '=', self.tahun-1),('state','=','Confirm'),('tipe_budget','=','opex')])
    #         else:
    #             if self.biro:
    #                 budgets = self.env['mcs.budget.coa'].search(
    #                     [('department', '=', self.department.id),('biro', '=', self.biro.id),
    #                      ('tahun', '=', self.tahun-1),('state','=','Review'),('tipe_budget','=','opex')])
    #                 if not budgets: 
              
    #                     budgets = self.env['mcs.budget.coa'].search(
    #                     [('department', '=', self.department.id), ('biro', '=', self.biro.id),('tahun', '=', self.tahun-1),('state','=','Confirm'),('tipe_budget','=','opex')])

    #         if budgets:
    #             for budget in budgets:
    #                 template_line.append([0, 0, {
    #                     'review_id': self.id,
    #                     'budget_id': budget.id,
    #                     'kode_perkiraan_id': budget.kode_coa.id,
    #                     'rkap':budget.total_anggaran,
    #                     'rkap_review': budget.total_anggaran + (self.persentase / 100 * budget.total_anggaran)
    #                 }])
    #         self.review_ids=template_line

        

    # def act_draft(self):
    #     self.state = 'confirm'


    # def act_confirm(self):
    #     if self.type =='review':
    #         if self.biro:
    #             budget = self.env['mcs.budget.coa'].search([('department','=',self.department.id),
    #                                                     ('tahun','=',self.tahun),
    #                                                     ('biro','=',self.biro.id),
    #                                                     ('state', '=', 'Review'),('tipe_budget','=','opex')])
    #         else:
    #             budget = self.env['mcs.budget.coa'].search([('department', '=', self.department.id),
    #                                                     ('tahun', '=', self.tahun),
    #                                                     ('state', '=', 'Review'),('tipe_budget','=','opex')])

    #         if budget:
    #             for x in budget:
    #                 del_budget = """ DELETE from mcs_budget_coa where id = %s""" %x.id

    #                 self._cr.execute(del_budget)

    #         for x in self.review_ids:

    #             spl = x.kode_perkiraan.code[0:4]
    #             grup = self.env['mcs.budget.parent'].search([('name','ilike',spl)],limit=1)
    #             budget_id = self.env['mcs.budget.coa'].create({
    #                                                 'tahun' : self.tahun,
    #                                                 'tipe_budget' :'opex',
    #                                                 'department' : self.department.id,
    #                                                 'biro' :self.biro.id or None,
    #                                                 'kode_coa':x.kode_perkiraan.id,
    #                                                 'state': 'Review',
    #                                                 'grup_akun':grup.id,
    #                                                 'bulan_review': self.bulan
    #                                                 })
    #             for product in x.detail_ids:
    #                 product_id = self.env['mcs.budget.coa.detail'].create({
    #                     'coa_id': budget_id.id,
    #                     'pekerjaan': product.product_id.id,
    #                     'vol': product.vol,
    #                     'satuan' : product.satuan,
    #                     'harga_satuan':product.harga_satuan,
    #                     'anggaran': product.anggaran,
    #                     'is_beban':product.is_beban,
    #                     'beban':product.beban,
    #                     'total_anggaran':product.total_anggaran,
    #                     'total_beban':product.total_beban,
    #                     'status_generate':True
    #                 })

    #                 for bulan in product.line_ids:
    #                     bulan = self.env['mcs.budget.coa.detail.line'].create({
    #                         'detail_id':product_id.id,
    #                         'bulan':bulan.bulan,
    #                         'anggaran':bulan.prognosa,
    #                         'sequence': bulan.bulan

    #                     })
    #                 for beban in product.beban_ids:
    #                     beban = self.env['mcs.budget.coa.detail.beban'].create({
    #                         'detail_id':product_id.id,
    #                         'branch_id': beban.branch_id.id,
    #                         'persen':beban.persen,
    #                         'anggaran':beban.anggaran,
    #                     })
    #             budget_id.act_generate()
    #         result = self.state = 'reviewed'
    #     if self.type =='rkap':
    #         if self.biro:
    #             budget = self.env['mcs.budget.coa'].search([('department','=',self.department.id),
    #                                                     ('tahun','=',self.tahun-1),
    #                                                     ('biro','=',self.biro.id),
    #                                                     ('state', '=', 'Review'),('tipe_budget','=','opex')])
    #             if not budget:
    #                 budget = self.env['mcs.budget.coa'].search([('department','=',self.department.id),
    #                                     ('tahun','=',self.tahun-1),
    #                                     ('biro','=',self.biro.id),
    #                                     ('state', '=', 'Confirm'),('tipe_budget','=','opex')])
    #         if not self.biro:
    #             budget = self.env['mcs.budget.coa'].search([('department', '=', self.department.id),
    #                                                     ('tahun', '=', self.tahun-1),
    #                                                     ('state', '=', 'Confirm'),('tipe_budget','=','opex')])
    #             if not budget:
    #                 budget = self.env['mcs.budget.coa'].search([('department', '=', self.department.id),
    #                                     ('tahun', '=', self.tahun-1),
    #                                     ('state', '=', 'Review'),('tipe_budget','=','opex')])


    #         for x in self.review_ids:

    #             spl = x.kode_perkiraan_id.code[0:4]
    #             grup = self.env['mcs.budget.parent'].search([('name','ilike',spl)],limit=1)
    #             budget_id = self.env['mcs.budget.coa'].create({
    #                                                 'tahun' : self.tahun,
    #                                                 'tipe_budget' :'opex',
    #                                                 'department' : self.department.id,
    #                                                 'biro' :self.biro.id or None,
    #                                                 'kode_coa':x.kode_perkiraan_id.id,
    #                                                 'state': 'Confirm',
    #                                                 'grup_akun':grup.id
                                                   
    #                                                 })
    #             for product in x.detail_ids:
    #                 product_id = self.env['mcs.budget.coa.detail'].create({
    #                     'coa_id': budget_id.id,
    #                     'pekerjaan': product.product_id.id,
    #                     'vol': product.vol,
    #                     'satuan' : product.satuan,
    #                     'harga_satuan':product.harga_satuan,
    #                     'anggaran': product.anggaran,
    #                     'is_beban':product.is_beban,
    #                     'beban':product.beban,
    #                     'total_anggaran':product.total_anggaran,
    #                     'total_beban':product.total_beban,
    #                     'status_generate':True
    #                 })
    #                 total_prognosa =0.0
    #                 for bulan in product.line_ids:
    #                     bulan = self.env['mcs.budget.coa.detail.line'].create({
    #                         'detail_id':product_id.id,
    #                         'bulan':bulan.bulan,
    #                         'anggaran':bulan.nilai_rkap,
    #                         'sequence': bulan.bulan

    #                     })

    #                     if x.budget_id.id:
    #                         update_budget = """ update mcs_budget_bulan 
    #                         set prognosa=(
    #                             select sum(data.prognosa) from mcs_budget_review_line_prognosa data
    #                             left join review_line_detail line on line.id=data.review_id
    #                             left join mcs_budget_review_line rev on rev.id=line.line_id
    #                             left join mcs_budget_coa budget on budget.id=rev.budget_id
    #                             where budget.id=%s and data.bulan=%s
    #                             group by budget.id)
                                
    #                             where coa_id=%s and bulan=%s """ %(x.budget_id.id,bulan.bulan,x.budget_id.id,bulan.bulan)

    #                         self._cr.execute(update_budget)
    #                 for beban in product.beban_ids:
    #                     beban = self.env['mcs.budget.coa.detail.beban'].create({
    #                         'detail_id':product_id.id,
    #                         'branch_id': beban.branch_id.id,
    #                         'persen':beban.persen,
    #                         'anggaran':beban.anggaran,
    #                     })
    #             budget_id.act_generate()
            
    #         result = self.state = 'rkap'
    #     return result

    # @api.depends('type')
    # def act_generate(self):
    #     if self.status_generate == False and self.type=='review':
    #         if self.review_ids:
    #             for x in self.review_ids:
    #                 if x.budget_id:
    #                     for data in x.budget_id.detail_ids:
    #                         product_id  =self.env['review.line.detail'].create({
    #                                     'line_id': x.id,
    #                                     'budget_detail_id': data.id,
    #                                     'product_id': data.pekerjaan.id,
    #                                     'vol': data.vol,
    #                                     'satuan': data.satuan,
    #                                     'harga_satuan': data.harga_satuan,
    #                                     'anggaran': data.anggaran,
    #                                     'is_beban': data.is_beban,
    #                                     'beban': data.beban,
    #                                     'total_anggaran': data.total_anggaran,
    #                                     'total_beban': data.total_beban,
    #                                     'total_rencana': data.vol * data.harga_satuan,
    #                                     'status_generate': True
    #                                 })

    #                         for bln in data.line_ids:

    #                             if self.biro:
    #                                 query = """
    #                                 select sum(invl.price_subtotal)            
    #                                     from account_invoice_line invl                            
    #                                     left join account_invoice inv on inv.id=invl.invoice_id
    #                                     left join account_account coa on coa.id=invl.account_id
    #                                     left join product_product product on product.id=invl.product_id
    #                                     where to_char(inv.date_invoice,'yyyy')= '%s'  and to_char(inv.date_invoice,'fmMM')='%s'
    #                                     and inv.biro=%s and inv.branch_id=%s and invl.account_id=%s  and invl.product_id=%s  

    #                                 """ % (self.tahun, bln.bulan, self.biro.id, self.department.id, x.kode_perkiraan.id, product_id.product_id.id)
    #                             elif not self.biro:
    #                                 query = """
    #                                     select
    #                                     sum(invl.price_subtotal)
    #                                     from account_invoice_line invl
    #                                     left join account_invoice inv on inv.id = invl.invoice_id
    #                                     left join account_account coa on coa.id = invl.account_id
    #                                     left join product_product product on product.id = invl.product_id
    #                                     where to_char(inv.date_invoice, 'yyyy') = '%s' and to_char(inv.date_invoice,'fmMM') = '%s'
    #                                     and inv.branch_id = % s and invl.account_id = % s and invl.product_id = % s
    #                                     """% (self.tahun, bln.bulan,self.department.id, x.kode_perkiraan.id,product_id.product_id.id)
    #                             self._cr.execute(query)
    #                             hasil = 0.0
    #                             hasil = self._cr.fetchone()[0]
    #                             self.env['mcs.budget.review.line.prognosa'].create({
    #                                 'review_id': product_id.id,
    #                                 'bulan': bln.bulan,
    #                                 'rencana': bln.anggaran,
    #                                 'realisasi': hasil,
    #                                 'prognosa': bln.anggaran,
    #                                 })
    #                         for beban in data.beban_ids:

    #                             self.env['review.beban'].create({
    #                                 'detail_id': product_id.id,
    #                                 'detil_beban_id': beban.id,
    #                                 'total_rencana':product_id.total_rencana,
    #                                  'branch_id': beban.branch_id.id,
    #                                   'persen': beban.persen,
    #                                 'anggaran': beban.anggaran
    #                             })
    #             self.status_generate = True
    #     if self.status_generate == False and self.type=='rkap':
    #         if self.review_ids:
    #             for x in self.review_ids:
    #                 if x.budget_id:
    #                     for data in x.budget_id.detail_ids:
    #                         product_id  =self.env['review.line.detail'].create({
    #                                     'line_id': x.id,
    #                                     'budget_detail_id': data.id,
    #                                     'product_id': data.pekerjaan.id,
    #                                     'vol': data.vol,
    #                                     'satuan': data.satuan,
    #                                     'harga_satuan': data.harga_satuan,
    #                                     'anggaran': data.anggaran,
    #                                     'is_beban': data.is_beban,
    #                                     'beban': data.beban,
    #                                     'total_anggaran': data.total_anggaran,
    #                                     'total_beban': data.total_beban,
    #                                     'total_rencana': data.vol * data.harga_satuan,
    #                                     'status_generate': True
    #                                 })
    #                         print(product_id)

    #                         for bln in data.line_ids:

    #                             if self.biro:
    #                                 query = """
    #                                 select sum(invl.price_subtotal)            
    #                                     from account_invoice_line invl                            
    #                                     left join account_invoice inv on inv.id=invl.invoice_id
    #                                     left join account_account coa on coa.id=invl.account_id
    #                                     left join product_product product on product.id=invl.product_id
    #                                     where to_char(inv.date_invoice,'yyyy')= '%s'  and to_char(inv.date_invoice,'fmMM')='%s'
    #                                     and inv.biro=%s and inv.branch_id=%s and invl.account_id=%s  and invl.product_id=%s  

    #                                 """ % (self.tahun-1, bln.bulan, self.biro.id, self.department.id, x.kode_perkiraan.id, product_id.product_id.id)
    #                             elif not self.biro:
    #                                 query = """
    #                                     select
    #                                     sum(invl.price_subtotal)
    #                                     from account_invoice_line invl
    #                                     left join account_invoice inv on inv.id = invl.invoice_id
    #                                     left join account_account coa on coa.id = invl.account_id
    #                                     left join product_product product on product.id = invl.product_id
    #                                     where to_char(inv.date_invoice, 'yyyy') = '%s' and to_char(inv.date_invoice,'fmMM') = '%s'
    #                                     and inv.branch_id = % s and invl.account_id = % s and invl.product_id = % s
    #                                     """% (self.tahun-1, bln.bulan,self.department.id, x.kode_perkiraan.id,product_id.product_id.id)
    #                             self._cr.execute(query)
    #                             hasil = 0.0
    #                             hasil = self._cr.fetchone()[0]
    #                             self.env['mcs.budget.review.line.prognosa'].create({
    #                                 'review_id': product_id.id,
    #                                 'bulan': bln.bulan,
    #                                 'rencana': bln.anggaran,
    #                                 'realisasi': hasil,
    #                                 'prognosa': bln.anggaran,
    #                                 'nilai_rkap': bln.anggaran,
    #                                 })
    #                         for beban in data.beban_ids:
    #                             print (beban)
    #                             self.env['review.beban'].create({
    #                                 'detail_id': product_id.id,
    #                                 'detil_beban_id': beban.id,
    #                                 'total_rencana':product_id.total_rencana,
    #                                  'branch_id': beban.branch_id.id,
    #                                 'persen': beban.persen,
    #                                 'anggaran': beban.anggaran
    #                             })
    #             self.status_generate = True

    # def name_get(self):
    #     res = []
    #     for record in self:
    #         biro = ""
    #         if record.biro:
    #             biro = " - %s" % record.biro.code
    #         tit = "[%s] [%s%s] - Review" % (
    #         record.tahun, record.department.code, biro)
    #         res.append((record.id, tit))
    #     return res

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=1000):
    #     args = args or []
    #     if name:
    #         # Be sure name_search is symetric to name_get
    #         args = ['|', ('code', operator, name), ('name', operator, name)] + args
    #     categories = self.search(args, limit=limit)
    #     return categories.name_get()
