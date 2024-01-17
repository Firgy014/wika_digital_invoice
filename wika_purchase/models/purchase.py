from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import AccessError, ValidationError
import pytz
from odoo.http import request


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
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    state = fields.Selection(selection_add=[
        ('po', 'PO'),
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved')
    ])
    po_type = fields.Char(string='Purchasing Doc Type')
    begin_date = fields.Date(string='Tgl Mulai Kontrak', required=True)
    end_date = fields.Date(string='Tgl Akhir Kontrak', required=True)
    document_ids = fields.One2many('wika.po.document.line', 'purchase_id', string='Purchase Order Document Lines')
    history_approval_ids = fields.One2many('wika.po.approval.line', 'purchase_id',
                                           string='Purchase Order Approval Lines')
    sap_doc_number = fields.Char(string='Nomor Kontrak', required=True)
    step_approve = fields.Integer(string='Step Approve')
    picking_count = fields.Integer(string='Picking', compute='_compute_picking_count')
    kurs = fields.Float(string='Kurs')
    unit_price_idr = fields.Float(string='Unit Price IDR')
    subtotal_idr = fields.Float(string='Subtotal IDR')
    currency_name = fields.Char(string='Currency Name', related='currency_id.name')

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
                    document_list.append((0, 0, {
                        'purchase_id': res.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                res.document_ids = document_list
            else:
                raise AccessError("Either approval and/or document settings are not found. Please configure it first in the settings menu.")

        return res

    def action_approve(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        documents_model = self.env['documents.document'].sudo()
        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
        if model_id:
            model_wika_id = self.env['wika.approval.setting'].search([('model_id', '=', model_id.id)], limit=1)

        if self.branch_id and not self.department_id:
            if user.branch_id.id == self.branch_id.id and model_wika_id:
                groups_line = self.env['wika.approval.setting.line'].search([
                    ('branch_id', '=', self.branch_id.id),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', model_wika_id.id)
                ], limit=1)

                groups_id = groups_line.groups_id

                for x in groups_id.users:
                    if x.id == self._uid:
                        cek = True


        # SUSUNAN APPROVAL
        # 1. base on project
        # 2. base on project & divisi
        # 3. base on divisi & department

        if self.branch_id and self.department_id and model_wika_id:
            print("-------------1-----------")
            if user.project_id.id == self.project_id.id:
                print("-------------2-----------")
                if user.branch_id.id == self.branch_id.id and user.department_id.id == self.department_id.id:
                    print("-------------3-----------")
                    print("STEP",self.branch_id.id)
                    print("STEP",self.step_approve)
                    print("STEP",self.step_approve)
                    print("STEP",self.step_approve)
                    print("STEP",self.step_approve)
                    groups_line = self.env['wika.approval.setting.line'].search([
                        ('branch_id', '=', self.branch_id.id),
                        ('department_id', '=', self.department_id.id),
                        ('project_id', '=', self.project_id.id),
                        ('sequence', '=', self.step_approve),
                        ('approval_id', '=', model_wika_id.id)
                    ], limit=1)

                    # Get group
                    groups_id = groups_line.groups_id
                    print("==GROUPS_LINE==", groups_line)
                    print("==GROUPS_ID==", groups_id)

                    for x in groups_id.users:
                        if x.id == self._uid:
                            cek = True

        print("==CEK==", cek)
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
                if self.activity_ids:
                    for x in self.activity_ids.filtered(lambda x: x.status == 'todo'):
                        x.status = 'approved'
            else:
                self.step_approve += 1

            self.env['wika.po.approval.line'].create({
                'user_id': self._uid,
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
        model_id = self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
        if model_id:
            model_wika_id = self.env['wika.approval.setting'].search([('model_id', '=', model_id.id)], limit=1)

        if user.branch_id.id == self.branch_id.id and model_wika_id:
            groups_line = self.env['wika.approval.setting.line'].search([
                ('branch_id', '=', self.branch_id.id),
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', model_wika_id.id)
            ], limit=1)
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
                'view_id': self.env.ref('wika_purchase.reject_wizard_form').id,
            }
            return action
        else:
            raise ValidationError('User Akses Anda tidak berhak Reject!')

    def action_submit(self):
        if self.document_ids.document != False:
            model_id = self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
            model_wika_id = self.env['wika.approval.setting'].search([('model_id', '=', model_id.id)], limit=1)
            user = self.env['res.users'].search([('branch_id', '=', self.branch_id.id)])

            if model_wika_id:
                groups_line = self.env['wika.approval.setting.line'].search([
                    ('branch_id', '=', self.branch_id.id),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', model_wika_id.id)
                ], limit=1)
                groups_id = groups_line.groups_id
                for x in groups_id.users:
                    self.env['mail.activity'].create({
                        'activity_type_id': 4,
                        'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1).id,
                        'res_id': self.id,
                        'user_id': x.id,
                        'summary': """Need Approval Document PO"""
                    })
                self.state = 'uploaded'
                self.step_approve += 1

        elif self.document_ids.document == False:
            self.document_ids.state = 'waiting'
            raise ValidationError('Anda belum mengunggah dokumen yang diperlukan!')

    def get_picking(self):
        self.ensure_one()
        view_id = self.env.ref("wika_inventory.stock_picking_tree_wika", raise_if_not_found=False)
        
        return {
            'name': _('GR/SES'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'stock.picking',
            'view_id': view_id.id,
            'res_id': self.id,
            'domain': [('po_id', '=', self.id)],  
            'context': {'default_po_id': self.id},
        }

    def _compute_picking_count(self):
        for record in self:
            record.picking_count = self.env['stock.picking'].search_count(
                [('po_id', '=', record.id)])

class PurchaseOrderDocumentLine(models.Model):
    _name = 'wika.po.document.line'
    _description = 'List Document PO'

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

    @api.constrains('document', 'filename')
    def _check_attachment_format(self):
        for record in self:
            if record.filename and not record.filename.lower().endswith('.pdf'):
                self.document = False
                self.state = 'waiting'
                raise ValidationError('Tidak dapat mengunggah file selain ekstensi PDF!')

class PurchaseOrderApprovalLine(models.Model):
    _name = 'wika.po.approval.line'
    _description = 'History Approval PO'

    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
