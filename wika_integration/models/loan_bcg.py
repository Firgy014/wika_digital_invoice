from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError
from datetime import datetime

class LoanBCG(models.Model):
    _name = 'loan.bcg'
    _description        ='Loan BCG'
    _rec_name           ='loan_item'


    date_period     = fields.Date(string='Date Period')
    loan_item       = fields.Char(string='Loan Item')
    loan_kriteria   = fields.Char(string='Loan Kriteria')
    loan_jenis      = fields.Char(string='Loan Jenis')
    loan_bank       =fields.Char(string='Loan Bank')
    loan_plafon     = fields.Float(string='Nilai Plafond')
    loan_prognosa   = fields.Float(string='Nilai Prognosa')
    loan_tgl_pembukaan  = fields.Date(string='Tanggal Pembukaan')
    loan_tgl_jatuh_tempo  = fields.Date(string='Tanggal Jatuh Tempo')
    loan_pembayaran     = fields.Float(string='Nilai Pembayaran')
    loan_kd_divisi          =fields.Char(string='Kode Divisi')
    loan_count_swift        = fields.Integer(string='Count Swift')
    loan_count_spk          = fields.Integer(string='Count SPK')
    loan_interest_rate      = fields.Float(string='Interest Rate')
    loan_der            = fields.Float(string='Loan Der')
    loan_cr             = fields.Float(string='Loan Cr')
    loan_dscr           = fields.Float(string='Loan Dscr')
    loan_gearing_ratio  = fields.Float(string='Loan Gearing Ratio')
    loan_iscr           = fields.Float(string='Loan Iscr')

class generate_loanbcg(models.TransientModel):
    _name = 'generate.loanbcg'
    _description = 'Wizard Generate Loan BCG'


    tanggal = fields.Date(string='Jatuh Tempo')


    def get_loan(self):
        loan=self.env['loan.bcg']

        if self.tanggal:
            where_tanggal = " 1=1 "
            where_tahun = " 1=1 "
            tahun_str= datetime.strptime(self.tanggal, "%Y-%m-%d")
            tahun = tahun_str.year
            where_tanggal = "'%s'" % self.tanggal
            where_tahun = "'%s'" %tahun

            query = """
                    --QUERY NCL REALISASI
                    
                    select 
                            to_char(ncl.tgl_swift,'yyyy-mm-01') as date_period,
                            'realisasi' as loan_item,
                            'NCL' as loan_kriteria,
                            pay.nama_jenis as loan_jenis,
                            bank.name as loan_bank,
                            0 as loan_plafon,
                            to_char(ncl.tgl_swift,'yyyy-mm-01') as loan_tgl_pembukaan,
                            to_char(pay.tgl_jatuh_tempo,'yyyy-mm-dd') as loan_tgl_jatuh_tempo,
                            sum(pay.nilai_pokok) as loan_pembayaran,
                            div.alias as divisi,
                            coalesce(count(pay.id),1) as count_swift,
                            coalesce(count(spk.code),1) as count_spk,		
                            coalesce(avg(ncl.rate_bunga),0) as interest_rate,
                            0 as loan_der,
                            0 as loan_cr,
                            0 as loan_dscr,
                            0 as loan_gearing_ratio,
                            0 as loan_iscr
                    from ncl_pembayaran pay
                            left join noncash_loan ncl on ncl.id=pay.loan_id
                            left join res_bank bank on bank.id=pay.bank_id
                            left join res_branch div on div.id=pay.branch_id
                            left join wika_project spk on spk.id=pay.project_loan_id
                    
                    
                    where pay.active='t' and pay.tgl_jatuh_tempo >= """+where_tanggal+""" and pay.nama_jenis!='BG'
                            group by loan_jenis,loan_bank,divisi,loan_tgl_pembukaan,loan_tgl_jatuh_tempo,date_period
                    
                    --QUERY CL REALISASI
                    
                    UNION ALL
                    
                    select 
                            to_char(cl.tgl_mulai,'yyyy-mm-01') as date_period,
                            'realisasi' as loan_item,
                            'CL' as loan_kriteria,
                            jenis.nama as loan_jenis,
                            bank.name as loan_bank,
                            0 as loan_plafon,
                            to_char(cl.tgl_mulai,'yyyy-mm-01') as loan_tgl_pembukaan,
                            to_char(pay.tgl_jatuh_tempo,'yyyy-mm-dd') as loan_tgl_jatuh_tempo,
                            sum(pay.nilai_pokok) as loan_pembayaran,
                            'A' as divisi,
                            0 as count_swift,
                            0 as count_spk,
                            coalesce(avg(cl.rate_bunga),0) as interest_rate,
                             0 as loan_der,
                            0 as loan_cr,
                            0 as loan_dscr,
                            0 as loan_gearing_ratio,
                            0 as loan_iscr
                    from cl_pembayaran pay
                            left join cash_loan cl on cl.id=pay.loan_id
                            left join res_bank bank on bank.id=pay.bank_id
                            left join loan_jenis jenis on jenis.id=cl.jenis_id
                    
                    where pay.tgl_jatuh_tempo >= """+where_tanggal+"""
                            group by loan_jenis,loan_bank,loan_tgl_pembukaan,loan_tgl_jatuh_tempo,date_period
                            
                    UNION ALL
                    select 
                                to_char(plaf.tgl_akhir,'yyyy-01-01') as date_period,
                                'plafond' as loan_item,
                                CASE 
                                WHEN plaf.tipe='Cash' THEN 'CL' 
                                WHEN plaf.tipe='Non Cash' THEN 'NCL'
                                END as loan_kriteria,
                                jenis.nama as loan_jenis,
                                bank.name as loan_bank,
                                line.nilai as loan_plafon,
                                NULL as loan_tgl_pembukaan,
                                NULL as loan_tgl_jatuh_tempo,
                                0 as loan_pembayaran,
                                NULL as divisi,
                                0 as count_swift,
                                0 as count_spk,
                                0 as interest_rate,
                                 plaf.loan_der as loan_der,
                                plaf.loan_cr as loan_cr,
                                plaf.loan_dscr as loan_dscr,
                                plaf.loan_gearing_ratio as loan_gearing_ratio,
                            plaf.loan_iscr as loan_iscr
                        from loan_plafond_detail line
                                    left join loan_plafond plaf on plaf.id= line.plafond_id
                                    left join res_bank bank on bank.id =plaf.bank_id
                                    left join loan_jenis jenis on jenis.id = line.jenis_id
                                    
                            where to_char(plaf.tgl_akhir,'yyyy')="""+where_tahun+""" and jenis.nama!='BG'
		
                           """
            list_data = []
            self._cr.execute(query)
            vals = self._cr.fetchall()
            for val in vals:
                data = {
                    'date_period': val[0],
                    'loan_item' : val[1],
                    'loan_kriteria' : val[2],
                    'loan_jenis' : val[3],
                    'loan_bank' : val[4],
                    'loan_plafon' : val[5],
                    'loan_prognosa' : 0,
                    'loan_tgl_pembukaan': val[6],
                    'loan_tgl_jatuh_tempo': val[7],
                    'loan_pembayaran': val[8],
                    'loan_kd_divisi': val[9],
                    'loan_count_swift': val[10],
                    'loan_count_spk': val[11],
                    'loan_interest_rate': val[12],
                    'loan_der':val[13],
                    'loan_cr':val[14],
                    'loan_dscr':val[15],
                    'loan_gearing_ratio':val[16],
                    'loan_iscr':val[17]

                }
                loan_bcg = self.env['loan.bcg'].sudo().create(data)


