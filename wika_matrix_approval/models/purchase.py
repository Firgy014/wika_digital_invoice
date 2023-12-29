from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import AccessError
import pytz

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

    # approval_history_ids = fields.One2many('wika.po.approval.line', 'purchase_id', string='Approved Lines')
    is_visible_button = fields.Boolean('Show Operation Buttons', default=True)
    branch_id = fields.Many2one('res.branch', string='Divisi')
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    state = fields.Selection(selection_add=[
        ('po', 'PO'), 
        ('uploaded', 'Uploaded'), 
        ('approved', 'Approved')
    ])
    po_type = fields.Char(string='Purchasing Doc Type')
    begin_date = fields.Date(string='Tgl Mulai Kontrak')
    end_date = fields.Date(string='Tgl Akhir Kontrak')
    document_ids = fields.One2many('wika.po.document.line', 'purchase_id', string='Purchase Order Document Lines')
    history_approval_ids = fields.One2many('wika.po.approval.line', 'purchase_id', string='Purchase Order Approval Lines')
    sap_doc_number = fields.Char(string='SAP Doc Number')

    def _get_matrix_approval_group(self):
        model_id = self.env['ir.model'].sudo().search([('name', '=', 'matrix.approval')], limit=1)
        group_id = self.env['res.groups'].sudo().search([
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

    @api.model_create_multi
    def create(self, vals_list):
        jkt_tz = pytz.timezone('Asia/Jakarta')
        model_model = self.env['ir.model'].sudo()
        approval_model = self.env['wika.matrix.approval'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        approval_setting_model = self.env['wika.approval.setting'].sudo()
        model_id = model_model.search([('model', '=', 'purchase.order')], limit=1)
        for vals in vals_list:
            res = super(PurchaseOrderInherit, self).create(vals)
            
            # Get Document Setting
            document_list = []
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

            # Get Approval Setting
            approval_list = []
            appr_setting_id = approval_setting_model.search([('model_id', '=', model_id.id)])

            if doc_setting_id:
                for document_line in doc_setting_id:
                    document_list.append((0,0, {
                        'purchase_id': res.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                res.document_ids = document_list
            else:
                raise AccessError("Either approval and/or document settings are not found. Please configure it first in the settings menu.")
            
            for group in res.env.user.groups_id:
                for menu in group.menu_access:
                    if 'Purchase' in menu.name: 
                        if len(menu.parent_path) > 4:
                            po_approval_group = group

            if appr_setting_id:
                for approval_line in appr_setting_id:
                    approval_list.append((0,0, {
                        'purchase_id': res.id,
                        'user_id': res.env.user.id,
                        'groups_id': po_approval_group.id,
                        'date': datetime.now(),
                        'note': f'Approved by {res.env.user.name} while creating a Purchase Order with reference: {res.name} at {datetime.now(jkt_tz).strftime("%d-%m-%Y")}.'
                    }))
                res.history_approval_ids = approval_list
            else:
                raise AccessError("Either approval and/or document settings are not found. Please configure it first in the settings menu.")

        return res

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

    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
