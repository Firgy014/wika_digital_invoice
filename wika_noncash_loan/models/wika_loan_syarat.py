from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

class invoice(models.Model):
    _name = 'wika.loan.invoice'
    _description='Loan Invoice'

    ncl_id          = fields.Many2one(comodel_name='wika.noncash.loan')
    name            = fields.Char(string="Nomor Invoice",required=True)
    tanggal         = fields.Date(string='Tanggal',required=True)
    nilai           = fields.Float(string='Nilai',required=True)
    nilai_asing    = fields.Float(string='Nilai Non IDR')
    ket             = fields.Char(string='Keterangan')
    doc_number      = fields.Char(string='Doc Number')
    run_date        = fields.Date(string='Run Date')

    invoice_id      = fields.Many2one(string='Invoice',comodel_name='account.move')


class syarat_dokumen(models.Model):
    _name = 'wika.loan.syarat'
    _rec_name = 'dokumen'
    _description='Loan Dokumen'

    jenis_id = fields.Many2one(comodel_name='wika.loan.jenis')
    ncl_id = fields.Many2one(comodel_name='wika.noncash.loan')
    dokumen = fields.Char(string="Persyaratan Dokumen")
    check_ada = fields.Boolean(string="Ada")
    check_tidak = fields.Boolean(string="Tidak Ada")
    dok_asli = fields.Boolean(string="Dokumen Asli")
    dok_copy = fields.Boolean(string="Dokumen Copy")
    keterangan = fields.Char(string="Keterangan")


class inherit_noncash_loan(models.Model):
    _inherit = 'wika.noncash.loan'

    syarat_ids = fields.One2many(comodel_name='wika.loan.syarat', inverse_name='ncl_id')
    invoice_ids = fields.One2many(comodel_name='wika.loan.invoice', inverse_name='ncl_id')

    # @api.multi
    # @api.onchange('jenis_id')
    # def _onchange_syarat(self):
    #     if self.stage_name != 'Pembukaan':
    #         if self.jenis_id:
    #             syarat_line=[]
    #             self.syarat_ids = None
    #             for x in self.jenis_id.syarat_ids:
    #                 syarat_line.append([0, 0, {
    #                     'dokumen': x.dokumen,
    #                     'keterangan': x.keterangan,
    #                 }])
    #             self.syarat_ids=syarat_line

# class inherit_loan_jenis(models.Model):
#     _inherit = 'loan.jenis'

#     syarat_ids = fields.One2many(comodel_name='loan.syarat', inverse_name='jenis_id')