# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import pycompat
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError
from odoo.tools.misc import unique


class res_branch(models.Model):
    _name = 'res.branch'
    _rec_name = 'code'
    _description = 'Operating Unit'

    code            = fields.Char(string="Kode", required=True)
    name            = fields.Char('Name', required=True)
    biro            = fields.Boolean(string='Department?')
    active          = fields.Boolean(string="Active",default=True)
    company_id      = fields.Many2one('res.company', 'Company', required=True)
    sequence           = fields.Char(string='Sequence', size=2)
    parent_id       = fields.Many2one('res.branch', string='Parent')
    partner_id      = fields.Many2one(comodel_name='res.partner', string='Partner')
    sap_code        = fields.Char(string="Profit Center")
    sap_code_cost   = fields.Char(string="Cost Center")
    ttd_ids        = fields.One2many(comodel_name='res.branch.ttd', ondelete='cascade', inverse_name='branch_id', index=True,
                               string='Master Tanda Tangan')
    rk_ids          = fields.One2many(comodel_name='res.branch.rk', inverse_name='parent_id', ondelete='cascade')
    kode_coa_rk_id  = fields.Many2one(comodel_name='account.account', string='Kode Perkiraan RK')
    eliminasi = fields.Boolean(string='Eliminasi?')
    anak_perusahaan = fields.Boolean(string='Anak Perusahaan?')

    # FMS REQUIRED FIELDS
    address = fields.Text('Address', size=252)
    telephone_no = fields.Char("Telephone No")
    alias = fields.Char(string='Alias', size=2)
    kode_jurnal = fields.Char(string='Kode Digit Jurnal', index=True)

    def _valid_field_parameter(self, field, name):
        # If the field has `task_dependency_tracking` on we track the changes made in the dependent task on the parent task
        return name == 'ondelete' or super()._valid_field_parameter(field, name)

    def get_ttd(self, laporan, sequence):
        ttd = self.env['res.branch.ttd'].search([('branch_id', '=', self.id),
                                                 ('laporan', '=', laporan),
                                                 ('sequence', '=', sequence)
                                                 ], limit=1)
        return ttd



class res_branch_ttd(models.Model):
    _name = 'res.branch.ttd'
    _description = 'Branch TTD Settings'


    branch_id       = fields.Many2one(string='Divisi', comodel_name='res.branch')
    laporan         = fields.Selection([('lembar_kendali_loan', 'Lembar Kendali Loan'),
                                        ('lembar_kendali_budget', 'Lembar Kendali Budget'),
                             ], string='Laporan')
    partner_id      = fields.Many2one('res.partner',string='Nama')
    sequence        = fields.Integer(string='Sequence')

class res_branch_rk(models.Model):
    _name = 'res.branch.rk'
    _description = 'Branch RK Settings'

    parent_id = fields.Many2one(comodel_name='res.branch', index=True)
    branch_id = fields.Many2one(comodel_name='res.branch', index=True)
    account_id = fields.Many2one(comodel_name='account.account')
