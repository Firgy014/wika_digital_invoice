from odoo import models, fields

class WikaPlafondBank(models.Model):
    _inherit = 'wika.plafond.bank'

    plaf_bank_ids = fields.One2many(comodel_name="wika.noncash.loan", ondelete='cascade', 
        inverse_name='plaf_id', domain=[('stage_name','not in',['Pembukaan','Diajukan','Ditolak','Cancel'])])
    plaf_bank_ids_H5 = fields.One2many(comodel_name="wika.ncl.pembayaran", ondelete='cascade', 
        inverse_name='plaf_id', domain=[ ('state', '!=', 'Lunas'),])
