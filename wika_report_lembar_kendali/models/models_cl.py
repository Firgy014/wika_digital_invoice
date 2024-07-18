from odoo import models, fields, api

from datetime import datetime, timedelta
# from odoo.osv import query
    
class WikaReportLembarKendaliCl(models.Model):
    _inherit = 'wika.cash.loan'

    def action_report(self):
        return self._print_report()
    
    def _print_report(self):
        report = self.env.ref('wika_report_lembar_kendali.report_print_lembar_kendali_cl').report_action(self)
        return report


    def get_report_satu(self):

        list_data = []
        today = fields.Date.today()
        # today_formatted = datetime.strptime(today, "%Y-%m-%d")
        if self.id:
            where_id = "cash_loan_id='%s'" % self.id
            #where_id3=" ncl.tgl_akhir>='2018-05-27'"
            #where_id4=" pay2.tgl_jatuh_tempo>='2018-05-27'"
            # where_id2=" tgl_jatuh_tempo>='%s'"%today_formatted

            query = (
                    """
                    select coalesce(jumlah_bayar,0),tgl_jatuh_tempo,rate_bunga,
                    (select coalesce(sum(jumlah_bayar),0)
                    from wika_cl_payment
                    where """
                + where_id
                + """ and state='Lunas'
                    )  as total,
                    state
                    from wika_cl_payment
                    where """
                + where_id
                + """
                    order by id asc
                """
            )

        self._cr.execute(query)
        vals = self._cr.fetchall()

        for val in vals:
            list_data.append(
                {
                    "nilai": val[0],
                    "tgl_jatuh_tempo": val[1],
                    "rate_bunga": val[2],
                    "total": val[3],
                    "state": val[4],
                }
            )
            print(val[0])
        return list_data

    def get_catatan(self):
        list_data = []
        pengajuan = 0.0
        for x in self.plafond_bank_id.plafond_id.plafond_ids:
            pengajuan += x.pengajuan
        plafond_bank = self.plafond_bank_id.plafond_id.jumlah
        plafond_bank_sisa = self.plafond_bank_id.plafond_id.sisa - pengajuan
        plafond_jenis = self.plafond_bank_id.nilai
        plafond_jenis_outs = self.plafond_bank_id.terpakai + self.plafond_bank_id.nilai_book + self.plafond_bank_id.pengajuan
        plafond_jenis_sisa = self.plafond_bank_id.sisa - self.plafond_bank_id.pengajuan
        # list_data.append({
        #     'jenis': 'Plafond Bank ' + self.bank_id.name,
        #     'nilai': plafond_bank,
        #     'kol': 2,
        #     'seq': 1
        # })
        list_data.append({
            'jenis': 'Plafond ' + self.jenis_id.nama,
            'nilai': plafond_jenis,
            'kol': 3,
            'seq': 2
        })
        list_data.append({
            'jenis': 'Outstanding ' + self.jenis_id.nama,
            'nilai': plafond_jenis_outs,
            'kol': 3,
            'seq': 3
        })
        list_data.append({
            'jenis': 'Sisa Plafond ' + self.jenis_id.nama,
            'nilai': plafond_jenis_sisa,
            'kol': 3,
            'seq': 4
        })

        for x in self.plafond_bank_id.plafond_id.plafond_ids:
            if x.jenis_id.id != self.jenis_id.id:
                list_data.append({
                    'jenis': 'Outstanding ' + x.jenis_id.nama,
                    'nilai': x.terpakai + x.nilai_book + x.pengajuan,
                    'kol': 2,
                    'seq': 5
                })
        #
        # list_data.append({
        #     'jenis': 'Sisa Plafond ' + self.bank_id.name,
        #     'nilai': plafond_bank_sisa,
        #     'kol': 2,
        #     'seq': 6
        # })

        list_data = sorted(list_data, key=lambda i: (i['seq']))
        return list_data

    def get_depart(self):
        depart= self.env['res.branch'].search(
            [('id', '=', 122)], limit=1)
        print ("CHECK TTD HAND DIVISI",depart)
        return depart