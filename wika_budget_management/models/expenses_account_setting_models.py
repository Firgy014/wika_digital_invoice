from odoo import models, fields
from datetime import datetime

class WikaSettingAccountExpense(models.Model):
    _name = 'wika.setting.account.expense'
    _description = 'Expenses Account Setting'

    account_id = fields.Many2one(comodel_name='account.account',string='Account')
    tipe_budget = fields.Selection([
        ('capex', 'Capex'),
        ('opex', 'Opex'),
        ('bad', 'BAD')
    ], string='Tipe Budget')