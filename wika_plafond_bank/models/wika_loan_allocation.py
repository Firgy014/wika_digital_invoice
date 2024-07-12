from odoo import models, fields, api

class WikaLoanAllocation(models.Model):
    _name = 'wika.loan.allocation'
    _description='Loan Allocation'

    name = fields.Char(string='Allocation Name')
    code = fields.Char(string='Code')