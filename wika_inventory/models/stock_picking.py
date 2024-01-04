from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import AccessError, ValidationError

class PickingInherit(models.Model):
    _inherit = "stock.picking"

    branch_id = fields.Many2one('res.branch', string='Divisi')
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    state = fields.Selection(selection_add=[
        ('waits', 'Waiting'), 
        ('uploaded', 'Uploaded'), 
        ('approved', 'Approved')
    ], string='Status')
    # pick_type = fields.Char(string='Type')
    pick_type = fields.Selection([
        ('ses', 'SES'), 
        ('gr', 'GR')
    ], string='Type')
    no_gr_ses = fields.Char(string='Nomor GR/SES')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    document_ids = fields.One2many('wika.picking.document.line', 'picking_id', string='List Document')
    history_approval_ids = fields.One2many('wika.picking.approval.line', 'picking_id', string='List Log')
    step_approve = fields.Integer(string='Step Approve')

    @api.model_create_multi
    def create(self, vals_list):
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'stock.picking')], limit=1)
        for vals in vals_list:
            res = super(PickingInherit, self).create(vals)
            
            # Get Document Setting
            document_list = []
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

            if doc_setting_id:
                for document_line in doc_setting_id:
                    document_list.append((0,0, {
                        'picking_id': res.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                res.document_ids = document_list
            else:
                raise AccessError("Either approval and/or document settings are not found. Please configure it first in the settings menu.")

        return res


    def action_approve(self):
        user = self.env['res.users'].search([('id','=',self._uid)], limit=1)
        cek = False
        model_id = self.env['ir.model'].search([('model','=', 'stock.picking')], limit=1)
        if model_id:
            model_wika_id = self.env['wika.approval.setting'].search([('model_id','=',  model_id.id)], limit=1)

        if user.branch_id.id==self.branch_id.id and model_wika_id:
            groups_line = self.env['wika.approval.setting.line'].search(
                [('branch_id', '=', self.branch_id.id), ('sequence',  '=', self.step_approve), ('approval_id', '=', model_wika_id.id )], limit=1)
            groups_id = groups_line.groups_id

            for x in groups_id.users:
                if x.id == self._uid:
                    cek = True

        if cek == True:
            if model_wika_id.total_approve == self.step_approve:
                self.state = 'approved'
            else:
                self.step_approve += 1

            self.env['wika.picking.approval.line'].create({
                'user_id': self._uid,
                'groups_id' :groups_id.id,
                'date': datetime.now(),
                'note': 'Approve',
                'picking_id': self.id
            })
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def action_reject(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        cek = False
        model_id = self.env['ir.model'].search([('model','=', 'stock.picking')], limit=1)
        if model_id:
            model_wika_id = self.env['wika.approval.setting'].search([('model_id','=',  model_id.id)], limit=1)

        if user.branch_id.id==self.branch_id.id and model_wika_id:
            groups_line = self.env['wika.approval.setting.line'].search(
                [('branch_id', '=', self.branch_id.id), ('sequence',  '=', self.step_approve), ('approval_id', '=', model_wika_id.id )], limit=1)
            groups_id = groups_line.groups_id
            for x in groups_id.users:
                if x.id == self._uid:
                    cek = True

        if cek == True:
            action = {
                'name': ('Reject Reason'),
                'type': "ir.actions.act_window",
                'res_model': "reject.wizard.picking",
                'view_type': "form",
                'target': 'new',
                'view_mode': "form",
                'context': {'groups_id': groups_id.id},
                'view_id': self.env.ref('wika_inventory.reject_wizard_picking_form').id,
            }
            return action
        else:
            raise ValidationError('User Akses Anda tidak berhak Reject!')

    def action_submit_pick(self):
        self.state = 'uploaded'
        self.step_approve += 1