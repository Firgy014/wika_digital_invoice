from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import AccessError, ValidationError
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
    step_approve = fields.Integer(string='Step Approve')

    def _get_matrix_approval_group(self):
    #     model_id = self.env['ir.model'].sudo().search([('name', '=', 'matrix.approval')], limit=1)
    #     group_id = self.env['res.groups'].sudo().search([
    #         ('model_access.model_id', '=', model_id.id)
    #     ])
    #     if group_id:
    #         return group_id
    #     else:
    #         return False
        return None

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
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'purchase.order')], limit=1)
        for vals in vals_list:
            res = super(PurchaseOrderInherit, self).create(vals)
            
            # Get Document Setting
            document_list = []
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

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

        return res



    def action_approve(self):
        documents_model = self.env['documents.document'].sudo()
        user = self.env['res.users'].search([('id','=',self._uid)], limit=1)
        cek = False
        model_id = self.env['ir.model'].search([('model','=', 'purchase.order')], limit=1)
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
                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'Purchase')], limit=1)
                if folder_id:
                    facet_id = self.env['documents.facet'].sudo().search([
                        ('name', '=', 'Kontrak'),
                        ('folder_id', '=', folder_id.id)
                    ], limit=1)
                    for doc in self.document_ids.filtered(lambda x: x.state == 'uploaded'):
                        doc.state = 'verified'
                        attachment_id = self.env['ir.attachment'].sudo().create({
                            'name': doc.filename,
                            'datas': doc.document,
                            'res_model': 'documents.document',
                        })
                        if attachment_id:
                            documents_model.create({
                                'attachment_id': attachment_id.id,
                                'folder_id': folder_id.id,
                                'tag_ids': facet_id.tag_ids.ids,
                                'partner_id': doc.purchase_id.partner_id.id,
                                'purchase_id': self.id,
                                'is_po_doc': True
                            })
                            
            else:
                self.step_approve += 1

            self.env['wika.po.approval.line'].create({'user_id': self._uid,
                'groups_id': groups_id.id,
                'date': datetime.now(),
                'note': 'Approve',
                'purchase_id': self.id
                })
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')


    def action_reject(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        cek = False
        model_id = self.env['ir.model'].search([('model','=', 'purchase.order')], limit=1)
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
                'res_model': "reject.wizard",
                'view_type': "form",
                'target': 'new',
                'view_mode': "form",
                'context': {'groups_id': groups_id.id},
                'view_id': self.env.ref('wika_matrix_approval.reject_wizard_form').id,
            }
            return action
        else:
            raise ValidationError('User Akses Anda tidak berhak Reject!')

    def action_submit(self):
        self.state = 'uploaded'
        self.step_approve += 1

    def _get_doc_tags_ids(self, model_name):
        tags_ids = list()
        tags_model = self.env['documents.tag'].sudo()
        facet_model = self.env['documents.facet'].sudo()
        facet_id = facet_model.search([('name', '=', model_name)], limit=1)
        
        if facet_id:
            tags_id = tags_model.create({
                'name': f'{model_name} Documents',
                'facet_id': facet_id.id
            })
            tags_ids.append(tags_id)
            return tags_ids

        else:
            facet_id = facet_model.create({'name':model_name})
            tags_id = tags_model.create({
                'name': f'{model_name} Documents',
                'facet_id': facet_id.id
            })
            tags_ids.append(tags_id)
            return tags_ids


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

    @api.onchange('document')
    def onchange_document_upload(self):
        if self.document:
            self.state = 'uploaded'

class PurchaseOrderApprovalLine(models.Model):
    _name = 'wika.po.approval.line'

    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
