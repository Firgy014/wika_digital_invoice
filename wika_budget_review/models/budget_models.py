import pytz
from pytz import timezone
from odoo import models, api, _, fields
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning
from babel.dates import format_datetime, format_date
from odoo.http import request, _logger
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class WikaMCSBudgetCOAInherit(models.Model):
    _inherit = 'wika.mcs.budget.coa'

    def get_biaya_divisi(self):
        date_invoice = datetime.strptime(self.tanggal_bad, "%Y-%m-%d")
        tahun = date_invoice.year
        bulan = date_invoice.month
        list_data = []
        tgl = '%s-01-01' % date_invoice.year
        tgl = str(tgl)
        where_branch = " %s " % self.department.id
        nobudget = str(self.nomor_budget)
        bulan_coa = self.env['wika.mcs.budget.coa'].search([
            ('department', '=', self.department.id),
            ('tahun', '=', tahun),
            ('tipe_budget', '=', 'opex'),
            ('state', '=', 'Review')],
            order='kode_coa asc',limit=1)

        if bulan_coa:
            if bulan < bulan_coa.bulan_review:
               budgets = self.env['wika.mcs.budget.coa'].search([
                    ('department', '=', self.department.id),
                    ('tahun', '=', tahun),
                    ('tipe_budget', '=', 'opex'),
                    ('state', '=', 'Confirm')],
                    order='kode_coa asc')
            elif bulan>= bulan_coa.bulan_review:
                budgets = self.env['wika.mcs.budget.coa'].search([
                    ('department', '=', self.department.id),
                    ('tahun', '=', tahun),
                    ('tipe_budget', '=', 'opex'),
                    ('state', '=', 'Review')],
                    order='kode_coa asc')
                
        else:
            budgets = self.env['wika.mcs.budget.coa'].search([
                ('department', '=', self.department.id),
                ('tahun', '=', tahun),
                ('tipe_budget', '=', 'opex'),
                ('state', '=', 'Confirm')],
                order='kode_coa asc')
        no = 0
        i = 0
        trkap = 0.0
        tri_lalu = 0.0
        tri_si = 0.0
        tri_tr = 0.0
        tri_ssi = 0.0
        tsisa = 0.0
        kode_coa = ""
        id_coa = ""
        coa_name = ""
        parent_name= ""
        rkap = 0.0
        parent_no = 0
        for budget in budgets:
            if i == 0:
                i += 1
                no += 1
                id_coa = budget.kode_coa.id
                kode_coa = budget.kode_coa.code
                coa_name = budget.kode_coa.name
                parent_name = budget.grup_akun.name
                parent_no += 1
                rkap += budget.total_anggaran
            if kode_coa != budget.kode_coa.code:

                #rkap = budget.total_anggaran
                ri_lalu = 0.0  # realisasi bulan lalu
                ri_si = 0.0  # realisasi saat ini
                ri_tr = 0.0  # persen realisasi terhadap rkap
                where_account = " %s " % id_coa
                query = """
                           SELECT
                            SUM(ri.price_subtotal)
                           FROM wika_vendor_bills_report ri
                            WHERE ri.tipe_budget in ('opex','bad') 
                                  and ri.branch_id=""" + where_branch + """                                     
                                  and ri.account_id=""" + where_account + """
                                  and ri.nomor_budget<'""" + nobudget + """'
                                  and ri.date_invoice>='""" + tgl + """'
                         group by ri.account_id,ri.branch_id
                          """
                self._cr.execute(query)
                realisasi = self._cr.fetchall()
                for x in realisasi:
                    ri_lalu += x[0]
                inv_si = self.env['wika.mcs.budget.coa.detail'].search([
                    ('coa_id', '=', self.id), ('account_id', '=', id_coa),
                ])
                for ini in inv_si:
                    ri_si += ini.total_anggaran

                ri_ssi = ri_lalu + ri_si  # realisasi sampai saat ini
                if rkap != 0:
                    ri_tr = (ri_ssi / rkap * 100) / 100

                sisa = rkap - ri_ssi  # sisa anggaran
                list_data.append({
                    'no': no,
                    'ket': 'DETAIL',
                    'program': coa_name,
                    'mata': kode_coa,
                    'parent' :parent_name,
                    'parent_no': parent_no,
                    'detail_no':999,
                    'rkap': rkap,
                    'ri_lalu': ri_lalu,
                    'ri_si': ri_si,
                    'ri_ssi': ri_ssi,
                    'ri_tr': ri_tr,
                    'sisa': sisa,
                })
                trkap += rkap
                tri_lalu += ri_lalu
                tri_si += ri_si
                tri_ssi += ri_ssi
                tsisa += sisa
                # tri_tr += ri_tr
                no += 1
                if trkap != 0:
                    tri_tr = tri_ssi / trkap * 100
                rkap = budget.total_anggaran
                id_coa = budget.kode_coa.id
                kode_coa = budget.kode_coa.code
                coa_name = budget.kode_coa.name
                parent_name = budget.grup_akun.name
                parent_no += 1
            else:
                if i !=1:
                    rkap += budget.total_anggaran
                i += 1

        # rkap = budget.total_anggaran
        ri_lalu = 0.0  # realisasi bulan lalu
        ri_si = 0.0  # realisasi saat ini
        ri_tr = 0.0  # persen realisasi terhadap rkap
        where_account = " %s " % id_coa
        query = """
                   SELECT sum(ri.price_subtotal)
                    FROM wika_vendor_bills_report ri
                    WHERE ri.tipe_budget in ('opex','bad') 
                          and ri.branch_id=""" + where_branch + """                                     
                          and ri.account_id=""" + where_account + """
                          and ri.nomor_budget!='""" + nobudget + """'
                          and ri.date_invoice>='""" + tgl + """'
                 group by ri.account_id,ri.branch_id
                  """
        self._cr.execute(query)

        realisasi = self._cr.fetchall()
        for x in realisasi:
            ri_lalu += x[0]
        inv_si = self.env['wika.mcs.budget.coa.detail'].search([
            ('coa_id', '=', self.id), ('account_id', '=', id_coa),
        ])
        for ini in inv_si:
            ri_si += ini.total_anggaran

        ri_ssi = ri_lalu + ri_si  # realisasi sampai saat ini
        if rkap != 0:
            ri_tr = (ri_ssi / rkap * 100) / 100

        sisa = rkap - ri_ssi  # sisa anggaran
        list_data.append({
            'no': no,
            'ket': 'DETAIL',
            'program': coa_name,
            'mata': kode_coa,
            'parent': parent_name,
            'parent_no':parent_no,
            'detail_no':999,
            'rkap': rkap,
            'ri_lalu': ri_lalu,
            'ri_si': ri_si,
            'ri_ssi': ri_ssi,
            'ri_tr': ri_tr,
            'sisa': sisa,
        })
        trkap += rkap
        tri_lalu += ri_lalu
        tri_si += ri_si
        tri_ssi += ri_ssi
        tsisa += sisa
        # tri_tr += ri_tr

        if trkap != 0:
            tri_tr = tri_ssi / trkap * 100
        parent_name= ""
        parent_no=0
        i = 0
        rkap = 0.0
        ri_lalu = 0.0
        ri_si = 0.0
        ri_tr = 0.0
        ri_ssi = 0.0
        sisa = 0.0
        list_data2=list_data.copy()
        for x in list_data2:

            if i == 0:
                parent_name=x['parent']
                parent_no = x['parent_no']
                rkap =x['rkap']
                ri_lalu = x['ri_lalu']
                ri_si = x['ri_si']
                ri_tr = x['ri_tr']
                ri_ssi =x['ri_ssi']
                sisa = x['sisa']
                i+=1
            if parent_name != x['parent']:

                if rkap != 0:
                    ri_tr = (ri_ssi / rkap * 100) / 100
                list_data.append({
                    'no': 1,
                    'ket': 'PARENT',
                    'program': '',
                    'mata': '',
                    'parent' :parent_name,
                    'parent_no': parent_no,
                    'detail_no': 1,
                    'rkap': rkap,
                    'ri_lalu': ri_lalu,
                    'ri_si': ri_si,
                    'ri_ssi': ri_ssi,
                    'ri_tr': ri_tr,
                    'sisa': sisa,
                })
                parent_name=x['parent']
                parent_no = x['parent_no']
                rkap =x['rkap']
                ri_lalu = x['ri_lalu']
                ri_si = x['ri_si']
                ri_tr = x['ri_tr']
                ri_ssi =x['ri_ssi']
                sisa = x['sisa']
                i+=1

            else:
                if i !=1:
                    rkap += x['rkap']
                    ri_lalu += x['ri_lalu']
                    ri_si += x['ri_si']
                    ri_tr += x['ri_tr']
                    ri_ssi += x['ri_ssi']
                    sisa += x['sisa']
                i +=1
        if rkap != 0:
            ri_tr = (ri_ssi / rkap * 100) / 100
        list_data.append({
            'no': 1,
            'ket': 'PARENT',
            'program': '',
            'mata': '',
            'parent': parent_name,
            'parent_no': parent_no,
            'detail_no': 1,
            'rkap': rkap,
            'ri_lalu': ri_lalu,
            'ri_si': ri_si,
            'ri_ssi': ri_ssi,
            'ri_tr': ri_tr,
            'sisa': sisa,
        })

        list_data.append({
            'no': 1,
            'ket': 'TOTAL',
            'program': '',
            'mata': '',
            'parent': 'TOTAL',
            'parent_no': 999,
            'detail_no': 1,
            'rkap': trkap,
            'ri_lalu': tri_lalu,
            'ri_si': tri_si,
            'ri_ssi': tri_ssi,
            'ri_tr': tri_tr,
            'sisa': tsisa,
        })
        list_data_sort=sorted(list_data,key=lambda i:(i['parent_no'],i['detail_no'],i['no']) )
        return list_data_sort

    def action_report_divisi(self):
        if not self.tanggal_bad:
            raise Warning(_('Harap Isi Tanggal Invoice!'))
        return self._print_report()
    
    def get_biaya(self):
        date_invoice = datetime.strptime(self.tanggal_bad, "%Y-%m-%d")
        tahun = date_invoice.year
        bulan = date_invoice.month
        list_data = []
        tgl = '%s-01-01' % date_invoice.year
        tgl = str(tgl)
        where_branch = " %s " % self.department.id
        where_biro = " %s " % self.biro.id
        nobudget = str(self.nomor_budget)
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
                    ('tahun', '=', tahun)
                    , ('tipe_budget', '=', 'opex'),
                    ('state', '=', 'Confirm')],
                    order='kode_coa asc')
            elif bulan >= bulan_coa.bulan_review:
                budgets = self.env['wika.mcs.budget.coa'].search([
                    ('department', '=', self.department.id),
                    ('biro', '=', self.biro.id),
                    ('tahun', '=', tahun),
                    ('tipe_budget', '=', 'opex'),
                    ('state', '=', 'Review')],
                    order='kode_coa asc')

        else:
            budgets = self.env['wika.mcs.budget.coa'].search([
                ('department', '=', self.department.id),
                ('biro', '=', self.biro.id),
                ('tahun', '=', tahun),
                ('tipe_budget', '=', 'opex'),
                ('state', '=', 'Confirm')],
                order='kode_coa asc')
        no = 0
        trkap = 0.0
        tri_lalu = 0.0
        tri_si = 0.0
        tri_tr = 0.0
        tri_ssi = 0.0
        tsisa = 0.0
        for budget in budgets:
            no += 1
            rkap = budget.total_anggaran
            ri_lalu = 0.0  # realisasi bulan lalu
            ri_si = 0.0  # realisasi saat ini
            ri_tr = 0.0  # persen realisasi terhadap rkap
            where_account = " %s " % budget.kode_coa.id
            query = """
                        SELECT sum(ri.price_subtotal)
                         FROM wika_vendor_bills_report ri
                         WHERE ri.tipe_budget in ('opex','bad') 
                               and ri.branch_id=""" + where_branch + """
                               and ri.biro=""" + where_biro + """ 
                               and ri.account_id=""" + where_account + """
                               and ri.nomor_budget!='""" + nobudget + """'
                               and ri.date_invoice>='""" + tgl + """'
                      group by ri.account_id,ri.branch_id,ri.biro

                       """
            self._cr.execute(query)
            realisasi = self._cr.fetchall()
            for x in realisasi:
                ri_lalu += x[0]
            inv_si = self.env['wika.mcs.budget.coa.detail'].search([
                ('coa_id', '=', self.id), ('account_id', '=', budget.kode_coa.id),
            ])
            for ini in inv_si:
                ri_si += ini.total_anggaran

            ri_ssi = ri_lalu + ri_si  # realisasi sampai saat ini
            if rkap != 0:
                ri_tr = (ri_ssi / rkap * 100)

            sisa = rkap - ri_ssi  # sisa anggaran
            list_data.append({
                'no': no,
                'program': budget.kode_coa.name,
                'mata': budget.kode_coa.code,
                'rkap': rkap,
                'ri_lalu': ri_lalu,
                'ri_si': ri_si,
                'ri_ssi': ri_ssi,
                'ri_tr': ri_tr,
                'sisa': sisa,
            })
            trkap += rkap
            tri_lalu += ri_lalu
            tri_si += ri_si
            tri_ssi += ri_ssi
            tsisa += sisa
            # tri_tr += ri_tr

            if trkap != 0:
                tri_tr = tri_ssi / trkap * 100

        list_data.append({
            'no': 'TOTAL',
            'program': '',
            'mata': '',
            'rkap': trkap,
            'ri_lalu': tri_lalu,
            'ri_si': tri_si,
            'ri_ssi': tri_ssi,
            'ri_tr': tri_tr,
            'sisa': tsisa,
        })
        return list_data

    def action_report_biro(self):
        if not self.tanggal_bad:
            raise Warning(_('Harap Isi Tanggal Invoice!'))
        return self._print_report_biro()

    tipe_budget = fields.Selection([
        ('capex', 'Capex'),
        ('opex', 'Opex'),
        ('bad', 'BAD')
    ], string='Tipe Budget')
    tanggal_bad = fields.Date(string='Tanggal',default=datetime.today())
    nomor_budget = fields.Char(string='Nomor Budget', store=True, readonly=True, copy=False)
    note = fields.Text(string='Note')
    
    @api.constrains('tipe_budget',
                    'tahun',
                    'state',
                    'kode_coa',
                    'department',
                    'biro')
    def check_data(self):
        for record in self:
            if not record.biro:
                obj = self.search([('tipe_budget', '=', record.tipe_budget),
                                   ('id', '!=', record.id),
                                   ('tahun', '=', record.tahun),
                                   ('state', '=', record.state),
                                   ('kode_coa', '=', record.kode_coa.id),
                                   ('department', '=', record.department.id),
                                   ])
            elif record.biro:
                obj = self.search([('tipe_budget', '=', record.tipe_budget),
                                   ('id', '!=', record.id),
                                   ('tahun', '=', record.tahun),
                                   ('state', '=', record.state),
                                   ('kode_coa', '=', record.kode_coa.id),
                                   ('department', '=', record.department.id),
                                   ('biro', '=', record.biro.id),
                                   ])

            if obj:
                raise ValidationError(_('Data Sudah ada!'))
                
    def confirm(self):
        for x in self:
            if x.tipe_budget!='bad':
                x.state = 'Confirm'
            else:
                model_ai = self.env['ir.model'].search([('model', '=', 'account.invoice')], limit=1)
                if x.tipe_budget and x.department:
                    sequence_id = self.env['ir.sequence'].search([('model_sequence', '=', model_ai.id),
                                                                  ('tipe_budget', '=', 'opex'),
                                                                  ('branch_id', '=', x.department.id)])
                    if sequence_id:
                        x.nomor_budget = self.env['ir.sequence'].next_by_code(sequence_id.code)
                        x.state = 'Confirm'
                    else:
                        raise ValidationError('Nomor Budget Belum Ada ! Silahkan Hubungi Admin')
                else:
                    raise ValidationError('Harap Isi Tipe budget!')

    @api.onchange('tipe_budget')
    def _onchange_account(self):
        for x in self:
            domain={}
            obj=self.env['wika.setting.account.expense'].search([('tipe_budget','=','bad')],limit=1)
            if x.tipe_budget == 'bad' :
                x.kode_coa= obj.account_id.id
                domain = {
                    'kode_coa': [('id', '=', obj.account_id.id)],
                }
            return {'domain': domain}


    @api.onchange('tahun', 'department', 'biro', 'tipe_budget')
    def _onchange_header(self):
        if self.tipe_budget =='bad' and self.tahun and self.department:
            template_line = []
            bulan_coa= None
            tgl = '%s-01-01' % self.tahun
            tgl_akhir = '%s-12-31' % self.tahun
            tgl = str(tgl)
            tgl_akhir = str(tgl_akhir)
            where_tahun= " %s " % self.tahun
            where_branch = " %s " % self.department.id
            if self.check_biro == False:
                pass
            #     query = """
            #         select 
            #             budget.kode_coa,
            #             coa.code,
            #             coa.name,
            #             COALESCE(budget.total_anggaran,0) as total_anggaran,
            #             min(detil.pekerjaan),
            #             (SELECT sum(ri.price_subtotal)
            #                          FROM wika_vendor_bills_report ri
            #                          WHERE ri.tipe_budget ='opex'
            #                          and ri.branch_id=budget.department
            #                          and ri.account_id=budget.kode_coa and ri.date_invoice between '""" + tgl + """' and '""" + tgl_akhir + """'
            #                     group by ri.account_id,ri.branch_id) as terpakai,
            #             COALESCE(budget.total_anggaran- (SELECT sum(ri.price_subtotal)
            #                      FROM wika_vendor_bills_report ri
            #                      WHERE ri.tipe_budget ='opex'
            #                              and ri.branch_id=budget.department                                    
            #                              and ri.account_id=budget.kode_coa and ri.date_invoice between '""" + tgl + """' and '""" + tgl_akhir + """'
            #             group by ri.account_id,ri.branch_id),0) as sisa
            #             from wika_mcs_budget_coa budget
            #             left join account_account coa on coa.id=budget.kode_coa
            #             left join wika_mcs_budget_coa_detail detil on detil.coa_id=budget.id
            #             where budget.tipe_budget ='opex' and budget.department=""" + where_branch + """ and tahun=""" + where_tahun + """ and budget.aktif='t'
            #                 and budget.total_anggaran>coalesce((SELECT sum(ri.price_subtotal)
            #                  FROM wika_vendor_bills_report ri
            #                  WHERE ri.tipe_budget ='opex'
            #                              and ri.branch_id=budget.department
            #                              and ri.account_id=budget.kode_coa and ri.date_invoice between '""" + tgl + """' and '""" + tgl_akhir + """'
            #             group by ri.account_id,ri.branch_id),0) 
            #     group by budget.kode_coa,budget.department,coa.code,coa.name,budget.total_anggaran
            #    """
            #     print (query)
            #     self.note=query
            #     self._cr.execute(query)
            #     bulan_coa = self._cr.fetchall()
            else:
                if self.biro:
                    pass
                #     where_biro= " %s " % self.biro.id
                #     query = """
                #     select 
                #         budget.kode_coa,
                #         coa.code,
                #         coa.name,
                #         COALESCE(budget.total_anggaran,0) as total_anggaran,
			    #         min(detil.pekerjaan),
                #         (SELECT sum(ri.price_subtotal)
                #                      FROM wika_vendor_bills_report ri
                #                      WHERE ri.tipe_budget ='opex'
                #                      and ri.branch_id=budget.department
                #                      and ri.biro=budget.biro
                #                      and ri.account_id=budget.kode_coa and ri.date_invoice between '""" + tgl + """' and '""" + tgl_akhir + """'
                #                 group by ri.account_id,ri.branch_id,ri.biro) as terpakai,
                #         COALESCE(budget.total_anggaran- (SELECT sum(ri.price_subtotal)
                #                  FROM wika_vendor_bills_report ri
                #                  WHERE ri.tipe_budget ='opex'
                #                              and ri.branch_id=budget.department
                #                              and ri.biro=budget.biro
                #                              and ri.account_id=budget.kode_coa and ri.date_invoice between '""" + tgl + """' and '""" + tgl_akhir + """'
                #             group by ri.account_id,ri.branch_id,ri.biro),0) as sisa
                #         from wika_mcs_budget_coa budget
                #         left join account_account coa on coa.id=budget.kode_coa
                #         left join wika_mcs_budget_coa_detail detil on detil.coa_id=budget.id
                #         where  budget.tipe_budget ='opex' and budget.department=""" + where_branch + """ and budget.biro=""" + where_biro + """and tahun=""" + where_tahun + """ and budget.aktif='t'
                #             and budget.total_anggaran>coalesce((SELECT sum(ri.price_subtotal)
				# 			 FROM wika_vendor_bills_report ri
				# 			 WHERE ri.tipe_budget ='opex'
				# 						 and ri.branch_id=budget.department
				# 						 and ri.biro=budget.biro
				# 						 and ri.account_id=budget.kode_coa and ri.date_invoice between '""" + tgl + """' and '""" + tgl_akhir + """'
				# 		group by ri.account_id,ri.branch_id,ri.biro),0) 
				# group by budget.kode_coa,budget.department,budget.biro,coa.code,coa.name,budget.total_anggaran
                #         """
                #     self.note = query
                #     self._cr.execute(query)
                #     bulan_coa = self._cr.fetchall()
            sisa=0
            if bulan_coa:
                for budget in bulan_coa:
                    if budget[6]<=0:
                        sisa= budget[3]
                    else:
                        sisa= budget[6]
                    template_line.append([0, 0, {
                        'coa_id': self.id,
                        'pekerjaan': budget[4],
                        'account_id': budget[0],
                        'vol': 1,
                        'is_beban': True,
                        'total_anggaran': sisa
                        }])
            self.detail_ids = template_line

    # def _print_report(self):
    #     report = self.env.ref('sc_bad.report_print_lembar_kendali_bad').report_action(self)
    #     return report


class WikaMCSBADDetailInherit(models.Model):
    _inherit = 'wika.mcs.budget.coa.detail'

    account_id = fields.Many2one(comodel_name='account.account',string='Account')

    @api.onchange('account_id','tipe_budget','pekerjaan')
    def _domain_line(self):
        domain = {}
        if self.coa_id.department and self.coa_id.tahun and self.coa_id.tipe_budget=='bad':
            obj = self.env['wika.mcs.budget.coa'].search([('tipe_budget', '=', 'opex'),
                                                     ('tahun', '=', self.coa_id.tahun),
                                                     ('department', '=', self.coa_id.department.id),
                                                     ('biro', '=', self.coa_id.biro.id),
                                                     ('state', '!=', 'Draft')])
            j = [x.kode_coa.id for x in obj]
            budget_line = self.env['wika.mcs.budget.coa.detail'].search([('coa_id', 'in', [x.id for x in obj])])
            y = [data.pekerjaan.id for data in budget_line]
            domain = {'domain': {
                'pekerjaan': [('id', 'in', y)],
                'account_id': [('id', 'in', j)],
            }}
        return domain