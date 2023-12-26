from odoo import api, fields, models, _
from datetime import datetime

class PurchaseOrderApprovalHistory(models.Model):
    _name = 'wika.purchase.order.approval.history'
    _description = 'List of Approved Orders'

    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    user_id = fields.Many2one('res.users', string='User')
    group_id = fields.Many2one('res.groups', string='Group')
    date = fields.Datetime(string='Date')
    note = fields.Text(string='Note')

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    approval_history_ids = fields.One2many('wika.purchase.order.approval.history', 'purchase_order_id', string='Approved Lines')
    is_visible_button = fields.Boolean('Show Operation Buttons', default=True)
    branch_id = fields.Many2one('res.branch', string='Divisi')
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    state = fields.Selection([
        ('po', 'PO'),
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved')
    ], string='Status')
    po_type = fields.Char(string='Purchasing Doc Type')
    end_date = fields.Date(string='Tgl Akhir Kontrak')
    document_ids = fields.One2many('wika.po.document.line', 'document_id', string='Purchase Order Document Lines')
    history_approval_ids = fields.One2many('wika.po.approval.line', 'approval_id', string='Purchase Order Approval Lines')

    def _get_matrix_approval_group(self):
        model_id = self.env['ir.model'].sudo().search([('name', '=', 'matrix.approval')], limit=1)
        group_id = self.env['res.groups'].sudo().search([
            # ('users', 'in', [self.env.user.id]),
            ('model_access.model_id', '=', model_id.id)
        ])
        if group_id:
            return group_id
        else:
            return False

    @api.onchange('partner_id')
    def _onchange_visibility(self):
        matrix_approval_group = self._get_matrix_approval_group()

        if matrix_approval_group:
            print("User has access to confirm a purchase order based on the matrix_approval_group")
        else:
            print("User has no access to confirm a purchase order based on the matrix_approval_group")


    def button_confirm(self):
        res = super(PurchaseOrderInherit, self).button_confirm()
        matrix_approval_group = self._get_matrix_approval_group()
        po_approval_model = self.env['wika.purchase.order.approval.history'].sudo()

        if matrix_approval_group:
        #     self.is_visible_button = True
        #     print("User has access to confirm a purchase order based on the matrix_approval_group")
        #     return res
        # else:
        #     self.is_visible_button = False
        #     print("User has no access to confirm a purchase order based on the matrix_approval_group")
        #     return {'type': 'ir.actions.act_window_close'}

        # if self.env.user.has_group('matrix_approval.access_matrix_approval'):
            po_approval_model.create({
                'purchase_order_id': self.id,
                'user_id': self.env.user.id,
                'group_id': matrix_approval_group.id,
                'date': datetime.now(),
                'note': f'Approved by {self.env.user.name} at {datetime.now().strftime("%d-%m-%Y")} for unconditional reason.'
            })
            return res
        else:
            return {
                'name': _('Access Denied'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('wika_matrix_approval.wizard_simple_form').id,
                'view_type': 'form',
                'res_model': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_message': _('You do not have the required access to confirm the Purchase Order.'),
                },
            }

    def button_cancel(self):
        res = super(PurchaseOrderInherit, self).button_cancel()
        matrix_approval_group = self._get_matrix_approval_group()
        po_approval_model = self.env['wika.purchase.order.approval.history'].sudo()

        if matrix_approval_group:
            print("User has access to cancel a purchase order based on the matrix_approval_group")
            po_approval_model.create({
                'purchase_order_id': self.id,
                'user_id': self.env.user.id,
                'group_id': matrix_approval_group.id,
                'date': datetime.now(),
                'note': f'Canceled by {self.env.user.name} at {datetime.now().strftime("%d-%m-%Y")} for unconditional reason.'
            })
            return res
        else:
            print("User has no access to cancel a purchase order based on the matrix_approval_group")
            return {'type': 'ir.actions.act_window_close'}

class PurchaseOrderDocumentLine(models.Model):
    _name = 'wika.po.document.line'

    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(attachment=True, store=True, string='Upload File')
    filename = fields.Char(string='File Name')
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verified', 'Verified')
    ], string='Status')

class PurchaseOrderApprovalLine(models.Model):
    _name = 'wika.po.approval.line'

    approval_id = fields.Many2one('wika.approval.setting', string='Approval')
    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
