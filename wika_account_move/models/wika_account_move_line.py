from odoo import fields, models

class WikaAccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    bap_line_id = fields.Many2one('wika.berita.acara.pembayaran.line', string='BAP Line Id', widget='many2one')
    # asw_tnat = fields.Char('asw tnat')