from odoo import models, fields, api,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning, AccessError


class WikaPartialPaymentRequest(models.Model):
    _name = 'wika.partial.payment.request'
    _description = 'Wika Partial Payment Request'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string='Nomor', readonly=True ,default='/')
    date = fields.Date(string='Tanggal', required=True, default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], readonly=True, string='status', default='draft')
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    invoice_id  = fields.Many2one(comodel_name='account.move',domain=[('state','=','approved'), ('sisa_partial', '!=', 0)])
    partner_id  = fields.Many2one(comodel_name='res.partner')
    total_invoice = fields.Float(string='Total Invoice')
    sisa_partial_amount = fields.Float(string='Sisa Partial Invoice')
    level = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat')
    ], string='Level', compute='_compute_level')
    check_biro = fields.Boolean(compute="_cek_biro")
    step_approve = fields.Integer(string='Step Approve',default=1)
    accounting_doc = fields.Char(string='Accounting Doc SAP')
    history_approval_ids = fields.One2many('wika.partial.approval.line', 'pr_id',
                                           string='Partial Payment Request  Approval')
    document_ids = fields.One2many('wika.partial.document.line', 'pr_id', string='Document Lines')
    approval_stage = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat'),
    ], string='Status Invoice')
    is_already_pr = fields.Boolean('is_already_pr')
    reference = fields.Char('Reference')
    no_doc_sap = fields.Char('No Doc SAP')
    year = fields.Char('Tahun')
    line_item_char = fields.Char('Line Item Char')
    partial_amount = fields.Float(string='Partial Amount')
    remaining_amount = fields.Float(string='Remaining Amount', compute='_compute_remaining_amount')
    payment_state = fields.Selection([
        ('not request', 'Not Request'),
        ('requested', 'Requested'),
    ], string='Payment State')
    payment_request_id = fields.Many2one('wika.payment.request', string='field_name')

    @api.depends('total_invoice', 'partial_amount')
    def _compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = record.total_invoice - record.partial_amount

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            sequence = self.env['ir.sequence'].next_by_code('wika.partial.payment.request')
            vals['name'] = sequence

        res = super(WikaPartialPaymentRequest, self).create(vals)
        res.assign_todo_first()
        return res

    # documents_count = fields.Integer(string='Total Doc', compute='_compute_documents_count')
    # @api.depends('invoice_ids')
    # def _compute_documents_count(self):
    #     for record in self:
    #         record.documents_count = self.env['documents.document'].search_count(
    #             [('invoice_id', 'in', record.invoice_ids.ids)])

    # def get_documents(self):
    #     self.ensure_one()
    #     view_kanban_id = self.env.ref("documents.document_view_kanban", raise_if_not_found=False)
    #
    #     view_tree_id = self.env.ref("documents.documents_view_list", raise_if_not_found=False)
    #
    #     return {
    #         'name': _('Documents'),
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'kanban,tree',
    #         'res_model': 'documents.document',
    #         'view_ids': [(view_kanban_id, 'kanban'), (view_tree_id.id, 'tree')],
    #         'res_id': self.id,
    #         'domain': [('invoice_id', 'in', self.invoice_ids.ids), ('folder_id', 'in', ('PO','GR/SES','BAP','Invoicing'))],
    #     }

    # @api.onchange('partial_amount')
    # def _update_amount_sisa_pr(self):
    #     if self.invoice_id:
    #         self.invoice_id._compute_amount_sisa_pr()

    @api.constrains('partial_amount', 'total_invoice')
    def _check_total_amount(self):
        for invoice in self:
            if invoice.partial_amount > invoice.total_invoice:
                raise UserError("Partial amount request lebih besar dari total invoice. Harap periksa kembali.")


    def assign_todo_first(self):
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'wika.partial.payment.request')], limit=1)
        for res in self:
            level=res.level
            first_user = False
            if level:
                approval_id = self.env['wika.approval.setting'].sudo().search(
                    [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=','pr')], limit=1)
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
                        'nomor_po': res.invoice_id.po_id.name,
                        'date_deadline': fields.Date.today() + timedelta(days=2),
                        'state': 'planned',
                        'summary': f"Need Upload Document {model_id.name}!"
                    })
                    res.approval_stage = level
            document_list = []
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

            if doc_setting_id:
                for document_line in doc_setting_id:
                    document_list.append((0, 0, {
                        'pr_id': res.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                res.document_ids = document_list
            else:
                raise AccessError(
                    "Either approval and/or document settings are not found. Please configure it first in the settings menu.")


    @api.depends('project_id', 'branch_id', 'department_id')
    def _compute_level(self):
        for res in self:
            level=''
            if res.project_id:
                level = 'Proyek'
            elif res.branch_id and not res.department_id and not res.project_id:
                level = 'Divisi Operasi'
            elif res.branch_id and res.department_id and not res.project_id:
                level = 'Divisi Fungsi'
            res.level = level

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

    # onchange otomatis incoive
    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     if self.partner_id:
    #         invoices = self.env['account.move'].search([('partner_id', '=', self.partner_id.id)])
    #         self.invoice_ids = [(6, 0, invoices.ids)]

    # @api.model
    # def create(self, vals):
    #     res =super(WikaPartialPaymentRequest, self).create(vals)
    #     res.name = self.env['ir.sequence'].next_by_code('wika.partial.payment.request')
    #     res.assign_todo_first()
    #     return  res

    # @api.depends('invoice_ids')
    # def compute_total(self):
    #     for record in self:
    #         total_amount = sum(record.invoice_ids.mapped('amount_total_signed'))
    #         record.total = total_amount

    @api.onchange('invoice_id')
    def _onchange_(self):
        if self.invoice_id:
            self.branch_id=self.invoice_id.branch_id.id
            self.project_id=self.invoice_id.project_id.id
            self.department_id=self.invoice_id.department_id.id
            self.partner_id=self.invoice_id.partner_id.id
            self.total_invoice=self.invoice_id.sisa_partial
            self.remaining_amount = self.total_invoice - self.partial_amount

    def action_submit(self):
        for record in self:
            if any(not line.document for line in record.document_ids):
                raise ValidationError('Document belum di unggah, mohon unggah file terlebih dahulu!')

        for record in self:
            if any(line.state == 'rejected' for line in record.document_ids):
                raise ValidationError('Document belum di ubah setelah reject, silahkan cek terlebih dahulu!')

        cek = False
        level = self.level
        model_model = self.env['ir.model'].sudo()
        model_id = model_model.search([('model', '=', 'wika.partial.payment.request')], limit=1)
        
        if level:
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('level', '=', level),
                 ('transaction_type', '=', 'pr'),('model_id', '=', model_id.id),], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu PR tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', 1),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            groups_id = approval_line_id.groups_id
            if groups_id:
                if self.activity_user_id.id == self._uid:
                    cek = True

        if cek == True:
            if self.activity_ids:
                for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                    if x.user_id.id == self._uid:
                        x.status = 'approved'
                        x.action_done()
                self.state = 'requested'
                self.approval_stage = approval_line_id.level_role
                self.step_approve += 1
                self.env['wika.partial.approval.line'].sudo().create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Submit Document',
                    'pr_id': self.id
                })
                groups_line = self.env['wika.approval.setting.line'].search([
                    ('level', '=', level),
                    ('sequence', '=', self.step_approve),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                groups_id_next = groups_line.groups_id
                if groups_id_next:
                    for x in groups_id_next.users:
                        if level == 'Proyek' and self.project_id in x.project_ids:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                            first_user = x.id
                    if first_user:
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': self.env['ir.model'].sudo().search(
                                [('model', '=', 'wika.partial.payment.request')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'nomor_po': self.invoice_id.po_id.name,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': """Need Approval Document Partial Payment Request"""
                        })
        else:
            raise ValidationError('User Akses Anda tidak berhak Submit!')

        
    def action_approve(self):
        user = self.env['res.users'].search([('id','=',self._uid)], limit=1)
        cek = False
        level=self.level
        documents_model = self.env['documents.document'].sudo()
        model_model = self.env['ir.model'].sudo()
        model_id = model_model.search([('model', '=', 'wika.partial.payment.request')], limit=1)
        approval_id = self.env['wika.approval.setting'].sudo().search(
            [('level', '=', level),
             ('transaction_type', '=', 'pr'),('model_id', '=', model_id.id),], limit=1)
        if not approval_id:
            raise ValidationError(
                'Approval Setting untuk menu PR tidak ditemukan. Silakan hubungi Administrator!')
        approval_line_id = self.env['wika.approval.setting.line'].search([
            ('sequence', '=', self.step_approve),
            ('approval_id', '=', approval_id.id)
        ], limit=1)
        groups_id = approval_line_id.groups_id
        if groups_id:
            for x in groups_id.users:
                if self.activity_user_id.id == self._uid:
                    cek = True

        if cek == True:
            if approval_id.total_approve == self.step_approve:
                self.state = 'approved'
                self.approval_stage = approval_line_id.level_role
                self.remaining_amount = self.total_invoice - self.partial_amount
        
                if self.remaining_amount > 0:
                    current_year = datetime.now().year
                    current_month = datetime.now().month
                    
                    previous_partial_name = self.name
                    previous_sequence_number = int(previous_partial_name.split('/')[-1])
                    new_sequence_number = previous_sequence_number + 1
                    new_name = f"Partial/{current_year}/{current_month:02d}/{new_sequence_number:03d}"
                    
                    remaining_total = self.remaining_amount
                    new_partial = self.env['wika.partial.payment.request'].create({
                        'invoice_id': self.invoice_id.id,
                        'partner_id': self.partner_id.id,
                        'partial_amount': remaining_total,
                        'total_invoice': self.remaining_amount,
                        'name': new_name,
                        'reference': previous_partial_name,
                        'date': fields.Date.today(),
                        'branch_id': self.branch_id.id,
                        'project_id': self.project_id.id,
                    })

                    previous_partial = self.env['wika.partial.payment.request'].search([('name', '=', previous_partial_name)], limit=1)
                    if previous_partial:
                        previous_partial.write({'name': previous_partial_name})

                self.env['wika.partial.approval.line'].create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Approved',
                    'pr_id': self.id
                })
                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'Invoice')], limit=1)
                # print("TESTTTTTTTTTTTTTTTTTTTTT", folder_id)
                if folder_id:
                    facet_id = self.env['documents.facet'].sudo().search([
                        ('name', '=', 'Documents'),
                        ('folder_id', '=', folder_id.id)
                    ], limit=1)
                    # print("TESTTTTTTTTTERRRRRRR", facet_id)
                    for doc in self.document_ids.filtered(lambda x: x.state in ('uploaded', 'rejected')):
                        doc.state = 'verified'
                        attachment_id = self.env['ir.attachment'].sudo().create({
                            'name': doc.filename,
                            'datas': doc.document,
                            'res_model': 'documents.document',
                        })
                        # print("SSSIIIIUUUUUUUUUUUUUUUUUU", attachment_id)
                        if attachment_id:
                            tag = self.env['documents.tag'].sudo().search([
                                ('facet_id', '=', facet_id.id),
                                ('name', '=', doc.document_id.name)
                            ], limit=1)
                            documents_model.create({
                                'attachment_id': attachment_id.id,
                                'folder_id': folder_id.id,
                                'tag_ids': tag.ids,
                                'partner_id': doc.bap_id.partner_id.id,
                                'purchase_id': self.invoice_id.po_id.id,
                            })
                if self.activity_ids:
                    for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                        if x.user_id.id == self._uid:
                            x.status = 'approved'
                            x.action_done()
            else:
                first_user = False
                # Createtodoactivity
                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level', '=', level),
                    ('sequence', '=', self.step_approve + 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                groups_id_next = groups_line_next.groups_id
                if groups_id_next:
                    for x in groups_id_next.users:
                        if level == 'Proyek' :
                            if self.project_id in x.project_ids or x.branch_id == self.branch_id or x.branch_id.parent_id.code == 'Pusat':
                                first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                            first_user = x.id

                    print(first_user)
                    if first_user:
                        self.step_approve += 1
                        self.approval_stage = approval_line_id.level_role
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': self.env['ir.model'].sudo().search(
                                [('model', '=', 'wika.partial.payment.request')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'nomor_po': self.invoice_id.po_id.name,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': """Need Approval Document Partial Payment Request"""
                        })
                        self.env['wika.partial.approval.line'].create({
                            'user_id': self._uid,
                            'groups_id': groups_id.id,
                            'date': datetime.now(),
                            'note': 'Verified',
                            'pr_id': self.id
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
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        cek = False
        level=self.level
        if level:
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('level', '=', level),
                 ('transaction_type', '=', 'pr')], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu Partial PR tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            groups_id = approval_line_id.groups_id
            if groups_id:
                for x in groups_id.users:
                    if self.activity_user_id.id == self._uid:
                        cek = True

        if cek == True:
            action = {
                'name': ('Reject Reason'),
                'type': "ir.actions.act_window",
                'res_model': "partial.reject.wizard.pr",
                'view_type': "form",
                'target': 'new',
                'view_mode': "form",
                'context': {'groups_id': groups_id.id},
                'view_id': self.env.ref('wika_payment_request.partial_reject_wizard_form').id,
            }
            return action
        else:
            raise ValidationError('User Akses Anda tidak berhak Reject!')



    # def unlink(self):
    #     for record in self:
    #         if record.state !='draft':
    #             raise ValidationError('Tidak dapat menghapus ketika status Payment Request dalam keadaan Request atau Approve')
    #     return super(WikaPartialPaymentRequest, self).unlink()

class WikaPrDocumentLine(models.Model):
    _name = 'wika.partial.document.line'
    _description = 'PartialDocument Line'

    pr_id = fields.Many2one('wika.partial.payment.request', string='pr id')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(string="Upload File", attachment=True, store=True)
    filename = fields.Char(string="File Name")
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], string='Status')


    @api.onchange('document')
    def onchange_document_upload(self):
        if self.document:
            if self.filename and not self.filename.lower().endswith('.pdf'):
                self.document = False
                self.filename = False
                self.state = 'waiting'
                raise ValidationError('Tidak dapat mengunggah file selain ekstensi PDF!')
            elif self.filename.lower().endswith('.pdf'):
                self.state = 'uploaded'

        else:
            self.document = False
            self.filename = False
            self.state = 'waiting'
            
class WikaPrApprovalLine(models.Model):
    _name = 'wika.partial.approval.line'
    _description = 'Wika PartialApproval Line'

    pr_id = fields.Many2one('wika.partial.payment.request', string='pr id')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')