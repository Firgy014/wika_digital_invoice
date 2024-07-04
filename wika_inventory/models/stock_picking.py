from odoo import models, fields, api, _
from datetime import datetime
from collections import defaultdict
from odoo.exceptions import AccessError, ValidationError
from datetime import datetime, timedelta
import logging, json
_logger = logging.getLogger(__name__)

class PickingInherit(models.Model):
    _inherit = "stock.picking"
    _description = "Stock Picking"

    partner_id = fields.Many2one('res.partner', string='Receive From', required=True)
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order', store=True)
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    po_id = fields.Many2one('purchase.order', string='Nomor PO')
    wika_state = fields.Selection([
        ('waits', 'Waiting'), 
        ('uploaded', 'Uploaded'), 
        ('approved', 'Approved'),
        ('rejected', 'Rejected')

    ], string='Wika Status', default='waits')
    pick_type = fields.Selection([
        ('ses', 'SES'), 
        ('gr', 'GR')
    ], string='Type', store=True)
    no_gr_ses = fields.Char(string='Nomor GR/SES')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    document_ids = fields.One2many('wika.picking.document.line', 'picking_id', string='List Document')
    history_approval_ids = fields.One2many('wika.picking.approval.line', 'picking_id', string='List Log')
    step_approve = fields.Integer(string='Step Approve',default=1)
    po_count = fields.Integer(string='Purchase Orders', compute='_compute_po_count')
    active = fields.Boolean(default=True)
    check_biro = fields.Boolean(compute="_cek_biro")
    movement_type = fields.Char(string='Movement Type')
    amount_bap = fields.Float('BAP Amount')
    # total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount')
    total_amount = fields.Float(string='Total Amount')
    product_uom_category_id = fields.Many2one(
        'uom.category', 
        string='Product UoM Category', 
        help='The unit of measure category for the products in this picking.'
    )
    account_id = fields.Many2one(
        'account.account', 
        string='Account',
        help='The account related to this picking.'
    )
    ref = fields.Char(
        string='Reference',  
        help='Reference for the picking operation.'
    )
    general_account_id = fields.Many2one(
        'account.account', 
        string='General Account', 
        help='The general account related to this picking.'
    )
    move_line_id = fields.Many2one(
        'stock.move.line', 
        string='Move Line', 
        help='The stock move line related to this picking.'
    )
    plan_id = fields.Integer('plan_id')
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency',  
        help='The currency related to this picking.'
    )
    unit_amount = fields.Float(
        'Unit Amount',
        default=0.0,
    )
    product_uom_id = fields.Many2one(
        'uom.uom', 
        string='Product Unit of Measure',
        help='The unit of measure for the product in this picking.'
    )
    amount = fields.Float(
        string='Amount', 
        help='The amount related to this picking.'
    )

    level = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat')
    ], string='Level', compute='_compute_level')

    @api.depends('project_id', 'branch_id', 'department_id')
    def _compute_level(self):
        for res in self:
            level = ''
            if res.project_id:
                level = 'Proyek'
            elif res.branch_id and not res.department_id and not res.project_id:
                level = 'Divisi Operasi'
            elif res.branch_id and res.department_id and not res.project_id:
                level = 'Divisi Fungsi'
            res.level = level

    @api.depends('move_ids.price_subtotal')
    def _compute_total_amount(self):
        for record in self:
            total_amount_value = sum(record.move_ids.mapped('price_subtotal'))
            if total_amount_value:
                record.total_amount = total_amount_value

    # @api.depends('bap_ids.price_subtotal')
    # def _compute_total_tax(self):
    #     for record in self:
    #         total_tax_value = sum(record.bap_ids.mapped('tax_amount'))
    #         record.total_tax = total_tax_value

    # @api.depends('total_amount', 'total_tax')
    # def _compute_grand_total(self):
    #     for record in self:
    #         record.grand_total = record.total_amount + record.total_tax

    @api.depends('department_id')
    def _cek_biro(self):
        for x in self:
            if x.department_id:
                biro = self.env['res.branch'].search([('parent_id', '=', x.department_id.id)])
                if biro:
                    x.check_biro = True
                else:
                    x.check_biro = False
            else:
                x.check_biro = False

    def assign_todo_first(self):
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'stock.picking')], limit=1)
        for res in self:
            level=res.level
            res.write({'wika_state':'waits'})
            first_user = False
            if level:
                approval_id = self.env['wika.approval.setting'].sudo().search(
                    [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',res.pick_type)], limit=1)
                approval_line_id = self.env['wika.approval.setting.line'].search([
                    ('sequence', '=', 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                groups_id = approval_line_id.groups_id
                if groups_id:
                    for x in groups_id.users:
                        if level == 'Proyek' and res.project_id in x.project_ids:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == res.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == res.department_id:
                            first_user = x.id
                print(first_user)
                #     # Createtodoactivity
                if first_user:
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': 4,
                        'res_model_id': model_id.id,
                        'res_id': res.id,
                        'user_id': first_user,
                        'nomor_po': res.po_id.name,
                        'date_deadline': fields.Date.today() + timedelta(days=2),
                        'state': 'planned',
                        'summary': f"Need Upload Document  {model_id.name}"
                    })

            # Get Document Setting
            document_list = []
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id),('transaction_type', '=', res.pick_type)])

            if doc_setting_id:
                for document_line in doc_setting_id:
                    document_list.append((0, 0, {
                        'picking_id': res.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                res.document_ids = document_list
            else:
                raise AccessError("Either approval and/or document settings are not found. Please configure it first in the settings menu.")

    def assign_company_to_move_ids(self, vals_list):
        for val in vals_list:
            for ids in val['move_ids_without_package']:
                    if 'company_id' in ids[2]:
                        ids[2]['company_id'] = 1
    
    @api.model_create_multi
    def create(self, vals_list):
        #self.assign_company_to_move_ids(vals_list)
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'stock.picking')], limit=1)
        for vals in vals_list:

            # if 'move_ids_without_package' in vals:
            #     for move_vals in vals['move_ids_without_package']:
            #         move_vals[2]['company_id'] = 1 if move_vals[2]['company_id'] is False else move_vals[2]['company_id']

            res = super(PickingInherit, self).create(vals)
            res.assign_todo_first()
        return res

    def action_approve(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        documents_model = self.env['documents.document'].sudo()
        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'stock.picking')], limit=1)
        level=self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'stock.picking')], limit=1)
            approval_id = self.env['wika.approval.setting'].search(
                [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',self.pick_type)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu GR/SES tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            groups_id = approval_line_id.groups_id
            _logger.info(str(self.activity_user_id.id) + "# === = === #" + str(self._uid))
            if self.activity_user_id.id == self._uid:
                cek=True

        if cek == True:
            if approval_id.total_approve == self.step_approve:
                self.wika_state = 'approved'
                self.env['wika.picking.approval.line'].create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Approved',
                    'picking_id': self.id
                })
                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'GR/SES')], limit=1)
                if folder_id:
                    facet_id = self.env['documents.facet'].sudo().search([
                        ('name', '=', 'Documents'),
                        ('folder_id', '=', folder_id.id)
                    ], limit=1)
                    for doc in self.document_ids.filtered(lambda x: x.state  in ('uploaded','rejected')):
                        doc.state = 'verified'
                        attachment_id = self.env['ir.attachment'].sudo().create({
                            'name': doc.filename,
                            'datas': doc.document,
                            'res_model': 'documents.document',
                        })
                        if attachment_id:
                            tag = self.env['documents.tag'].sudo().search([
                                ('facet_id', '=', facet_id.id),
                                ('name', '=', doc.document_id.name)
                            ], limit=1)
                            documents_model.create({
                                'attachment_id': attachment_id.id,
                                'folder_id': folder_id.id,
                                'tag_ids': tag.ids,
                                'partner_id': self.purchase_id.partner_id.id,
                                'purchase_id': self.purchase_id.id,
                                'picking_id': self.id,
                                'is_po_doc': True
                            })
                if self.activity_ids:
                    for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                        if x.user_id.id == self._uid:
                            _logger.info("# === groups === #" + str(x.status))
                            x.status = 'approved'
                            x.action_done()
            else:
                first_user=False
                # Createtodoactivity
                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level', '=', level),
                    ('sequence', '=', self.step_approve+1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                _logger.info("# === groups === #" + str(groups_line_next))
                groups_id_next = groups_line_next.groups_id
                if groups_id_next:
                    _logger.info("# === groups === #" + str(groups_id_next.name))
                    for x in groups_id_next.users:
                        if level == 'Proyek' and self.project_id in x.project_ids:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                            first_user = x.id

                    _logger.info("# === first_user === #" + str(first_user))
                    if first_user:
                        self.step_approve += 1
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': self.env['ir.model'].sudo().search(
                                [('model', '=', 'stock.picking')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'nomor_po': self.po_id.name,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status':'to_approve',
                            'summary': """Need Approval Document GR/SES"""
                        })
                        self.env['wika.picking.approval.line'].create({
                            'user_id': self._uid,
                            'groups_id': groups_id.id,
                            'date': datetime.now(),
                            'note': 'Approved',
                            'picking_id': self.id
                        })
                        if self.activity_ids:
                            for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                                if x.user_id.id == self._uid:
                                    x.status = 'approved'
                                    x.action_done()
                    else:
                        raise ValidationError('User Role Next Approval Belum di Setting!')
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def action_reject(self):
        cek = False
        level=self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'stock.picking')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level),
                 ('transaction_type', '=', self.pick_type)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu Purchase Orders tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            groups_id = approval_line_id.groups_id
            if groups_id:
                if self.activity_user_id.id == self._uid:
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
        if self.document_ids:
            for doc_line in self.document_ids:
                if doc_line.document == False:
                    raise ValidationError('Anda belum mengunggah dokumen yang diperlukan!')
            cek = False
            level=self.level
            if level:
                model_id = self.env['ir.model'].search([('model', '=', 'stock.picking')], limit=1)
                approval_id = self.env['wika.approval.setting'].sudo().search(
                    [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',self.pick_type)], limit=1)
                if not approval_id:
                    raise ValidationError(
                        'Approval Setting untuk menu Purchase Orders tidak ditemukan. Silakan hubungi Administrator!')
                approval_line_id = self.env['wika.approval.setting.line'].search([
                    ('sequence', '=', 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                _logger.info("# === approval_line_id === # "+ str(approval_line_id.groups_id))
                groups_id = approval_line_id.groups_id
                if groups_id:
                    _logger.info(str(self.activity_user_id.id) + "# === #"+ str(self._uid))
                    if self.activity_user_id.id == self._uid:
                        cek = True

            if cek == True:
                if self.activity_ids:
                    for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                        if x.user_id.id == self._uid:
                            x.status = 'approved'
                            x.action_done()
                    self.wika_state = 'uploaded'
                    self.step_approve += 1
                    self.env['wika.picking.approval.line'].sudo().create({
                        'user_id': self._uid,
                        'groups_id': groups_id.id,
                        'date': datetime.now(),
                        'note': 'Submit Document',
                        'picking_id': self.id
                    })
                    _logger.info("# === step_approve === # "+ str(self.step_approve))
                    groups_line = self.env['wika.approval.setting.line'].search([
                        ('level', '=', level),
                        ('sequence', '=', self.step_approve),
                        ('approval_id', '=', approval_id.id)
                    ], limit=1)
                    _logger.info("# === groups === # "+ str(groups_line))
                    groups_id_next = groups_line.groups_id
                    if groups_id_next:
                        _logger.info("# === groups_id_next === # "+ str(groups_id_next.name))
                        for x in groups_id_next.users:
                            if level == 'Proyek' and self.project_id in x.project_ids:
                                first_user = x.id
                            if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                                first_user = x.id
                            if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                                first_user = x.id
                        _logger.info("# === first_user === # "+ str(first_user))
                        if first_user:
                            self.env['mail.activity'].sudo().create({
                                'activity_type_id': 4,
                                'res_model_id': self.env['ir.model'].sudo().search(
                                    [('model', '=', 'stock.picking')], limit=1).id,
                                'res_id': self.id,
                                'user_id': first_user,
                                'nomor_po': self.po_id.name,
                                'date_deadline': fields.Date.today() + timedelta(days=2),
                                'state': 'planned',
                                'status': 'to_approve',
                                'summary': """Need Approval Document GR/SES"""
                            })

            else:
                raise ValidationError('User Akses Anda tidak berhak Submit!')

        else:
            raise ValidationError('Mohon untuk diisi terlebih dahulu Nama Penanda Tangan, Jabatan, Nama Penanda Tangan Vendor, Jabatan Vendor, Tgl Akhir Kontrak dan Nomor Kontrak.')


    def get_purchase(self):
        self.ensure_one()
        view_id = self.env.ref("wika_purchase.purchase_order_tree_wika", raise_if_not_found=False)

        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'purchase.order',
            'view_id': view_id.id,
            'target': 'main',
            'res_id': self.id,
            'domain': [('id', '=', self.po_id.id)],
        }

    def _compute_po_count(self):
        for record in self:
            record.po_count = self.env['purchase.order'].search_count(
                [('id', '=', record.po_id.id)])
            
    # @api.depends('move_type', 'immediate_transfer', 'move_ids.state', 'move_ids.picking_id')
    # def _compute_state(self):
    #     for rec in self:
    #         _logger.info("# === SP _compute_state === #" + str(self.state))
    #         res = super(PickingInherit, rec)._compute_state()
        
    #     return res
        