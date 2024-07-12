
from odoo import models, fields, api, exceptions
    
class WikaLoanStage(models.Model):
    _name           = 'wika.loan.stage'
    _description    = 'Master Stage Loan'
    _order          = "sequence asc"   
    
    name = fields.Char(string="Nama", required=True)   
    tipe = fields.Selection(string='Tipe', selection=[
        ('Cash', 'Cash'), ('Non Cash', 'Non Cash')
    ], required="True")           
    sequence = fields.Integer('Sequence', default=1)
    scf = fields.Boolean('SCF')
    bg = fields.Boolean('BG')
    jaminan = fields.Boolean('Jaminan')
    request = fields.Boolean('request')
    jumlah_approve = fields.Integer('Jumlah Approve')
    groups_ids = fields.One2many(comodel_name='wika.loan.stage.line',inverse_name='stage_id')

class WikaLoanStageLine(models.Model):
    _name = 'wika.loan.stage.line'

    stage_id = fields.Many2one(comodel_name='wika.loan.stage')
    groups_id = fields.Many2one(comodel_name='res.groups',required=True)
    sequence= fields.Integer(string='Sequence')
    
