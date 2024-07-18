from odoo import models, fields, api, _

class WikaEmployeeLoanDetails(models.Model):
    _name = 'wika.employee.loan.details'
    _description = 'Employee Loan Details'

    name = fields.Char(string='Name')