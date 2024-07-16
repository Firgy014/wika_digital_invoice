from odoo import models, fields, api, _

class WikaAccountAsset(models.Model):
    _inherit = 'account.asset'

    luas_tanah = fields.Char(string='Luas Tanah')
    tahun_beli = fields.Integer(striing='tahun Beli', size=4)
    no_bukti = fields.Char(string='No Bukti')
    merk = fields.Char(string='Merk')
    usia_tahun = fields.Integer(string='Usia Tahun')
    branch_id = fields.Many2one(comodel_name='res.branch', string='Department')
    biro = fields.Many2one('res.branch', 'Biro')
    check_biro = fields.Boolean(compute="_cek_biro")

    @api.onchange('branch_id')
    def domain_department(self):
        self.biro = None

    @api.depends('branch_id')
    def _cek_biro(self):
        for x in self:
            if x.branch_id:
                biro = self.env['res.branch'].search([('parent_id', '=', x.branch_id.id)])
                if biro:
                    x.check_biro = True
                else:
                    x.check_biro = False
            else:
                x.check_biro = False