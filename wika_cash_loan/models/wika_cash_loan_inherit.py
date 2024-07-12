from odoo import models, fields

class WikaPlafondBankInherited(models.Model):
    _inherit = 'wika.plafond.bank'

    plaf_bank_ids_cl = fields.One2many(comodel_name="wika.cash.loan", ondelete='cascade', 
        inverse_name='plaf_id', domain=[('stage_name','not in',['Pengajuan','Diajukan','Ditolak'])])
    plaf_bank_ids_H5_cl = fields.One2many(comodel_name="wika.cl.payment", ondelete='cascade', 
        inverse_name='plaf_id',domain=[ ('state', '!=', 'Lunas'),])

    def compute_total(self):
        for x in self:
            if x.tipe=='cash':
                x.total_h5=sum(line.nilai_pokok for line in x.plaf_bank_ids_H5_cl)
            else:
                x.total_h5=sum(line.nilai_pokok for line in x.plaf_bank_ids_H5)
            x.total_h5=x.total_h5/1000000
