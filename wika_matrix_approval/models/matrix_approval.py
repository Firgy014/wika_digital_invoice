from odoo import api, fields, models, _
from datetime import datetime
import pytz

class WikaApprovalSetting(models.Model):
    _name = 'wika.approval.setting'
    _description = 'Matrix Approval Setting'

    name = fields.Char(string='Approval Name', required=True, copy=False, readonly=True, index=True, default=lambda self: self._default_name())
    branch_id = fields.Many2one('res.branch', string='Branch')
    project_id = fields.Many2one('project.project', string='Project')
    model_id = fields.Many2one('ir.model', string='Akses Menu')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], string='Status')
    setting_line_ids = fields.One2many('wika.approval.setting.line', 'approval_id', string='Lines')
    total_approve = fields.Integer(string='Total Approve', compute = 'compute_total_approve')

    @api.model
    def _default_name(self):
        current_date_time = datetime.now(pytz.timezone('Asia/Jakarta'))
        formatted_date_time = current_date_time.strftime('%Y%m%d%H%M%S')
        return f"APR/{formatted_date_time}"

    @api.onchange('state')
    def _onchange_state(self):
        for record in self:
            if record.state == 'confirm':
                record.set_fields_readonly()

    def set_fields_readonly(self):
        for field_name, field in self.env['wika.approval.setting.line']._fields.items():
            # print(type(field_name))
            # print(field_name)
            # print(type(field))
            # print(field)
            # print("dirdirdir")
            # print(dir(field))
            # errorin
            if not field.related:
                self[field_name].readonly = True

    @api.depends('setting_line_ids')
    def compute_total_approve(self):
        for record in self:
            total_line = self.env['wika.approval.setting.line'].search_count([('approval_id',  '=' , record.id)])
            record.total_approve = total_line

class WikaApprovalSettingLine(models.Model):
    _name = 'wika.approval.setting.line'
    _description = 'Matrix Approval Setting Line'
    
    approval_id = fields.Many2one('wika.approval.setting', string='Approval Setting')
    branch_id = fields.Many2one('res.branch', string='Branch', related = 'approval_id.branch_id')
    sequence = fields.Integer(string='Sequence/Step')
    user_id = fields.Many2one('res.users', string='Approver/User')
    groups_id = fields.Many2one('res.groups', string='Role/Groups')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], string='Status', related='approval_id.state')