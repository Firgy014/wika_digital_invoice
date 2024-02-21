from odoo import models, fields, api,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning, AccessError


class WikaPaymentRequest(models.Model):
    _name = 'wika.payment.request'
    _description = 'Wika Payment Request'
    _inherit = ['mail.thread']

    name = fields.Char(string='Nomor Payment Request', readonly=True ,default='/')
    date = fields.Date(string='Tanggal Payement Request', required=True, default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Requested'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ], readonly=True, string='status', default='draft')
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    invoice_ids = fields.Many2many('account.move', string='Invoice', required=True)
    document_ids = fields.One2many('wika.pr.document.line', 'pr_id', string='Document Line')
    history_approval_ids = fields.One2many('wika.pr.approval.line', 'pr_id', string='Approval Line')
    total = fields.Integer(string='Total', compute='compute_total')
    step_approve = fields.Integer(string='Step Approve')
    reject_reason_pr = fields.Text(string='Reject Reason')
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)
    assignment = fields.Char('Assignment')
    reference = fields.Char('Reference')
    payment_block = fields.Selection([
        ('B', 'Default Invoice'),
        ('C', 'Pengajuan Ke Divisi'),
        ('D', 'Pengajuan Ke Pusat'),
        ('" "', 'Free For Payment (Sudah Approve)'),
        ('K', 'Dokumen Kembali'),
    ], string='Payment Block',default='B')
    #partner_id = fields.Many2one('res.partner', string='Vendor')
    payment_method = fields.Selection([
        ('transfer tunai', 'Transfer Tunai (TT)'),
        ('fasilitas', 'Fasilitas'),
    ], string='Payment Method')
    check_biro = fields.Boolean(compute="_cek_biro")
    level = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat')
    ], string='Level',compute='_compute_level')

    documents_count = fields.Integer(string='Total Doc', compute='_compute_documents_count')
    @api.depends('invoice_ids')
    def _compute_documents_count(self):
        for record in self:
            record.documents_count = self.env['documents.document'].search_count(
                [('invoice_id', 'in', record.invoice_ids.ids)])

    def get_documents(self):
        self.ensure_one()
        view_kanban_id = self.env.ref("documents.document_view_kanban", raise_if_not_found=False)

        view_tree_id = self.env.ref("documents.documents_view_list", raise_if_not_found=False)

        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree',
            'res_model': 'documents.document',
            'view_ids': [(view_kanban_id, 'kanban'), (view_tree_id.id, 'tree')],
            'res_id': self.id,
            'domain': [('invoice_id', 'in', self.invoice_ids.ids), ('folder_id', 'in', ('PO','GR/SES','BAP','Invoicing'))],
        }

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

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('wika.payment.request')
        return super(WikaPaymentRequest, self).create(vals)

    @api.depends('invoice_ids')
    def compute_total(self):
        for record in self:
            total_amount = sum(record.invoice_ids.mapped('amount_total_signed'))
            record.total = total_amount

    @api.onchange('invoice_ids')
    def _onchange_(self):
        if self.invoice_ids:
            model_model = self.env['ir.model'].sudo()
            document_setting_model = self.env['wika.document.setting'].sudo()
            model_id = model_model.search([('model', '=', 'wika.payment.request')], limit=1)
            print("invoice_ids----------TEST--------", model_id)
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

            if doc_setting_id:
                self.document_ids.unlink()

                document_list = []
                for document_line in doc_setting_id:
                    document_list.append((0, 0, {
                        'pr_id': self.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                self.document_ids = document_list
            else:
                raise AccessError("Data dokumen tidak ada!")

    def action_submit(self):
        # if any (doc.state != 'verif'  for doc in self.document_ids):
        #     raise UserError('Tidak bisa submit karena ada dokumen yang belum diverifikasi!')
        self.write({'state': 'request'})
        self.step_approve += 1
        model_id = self.env['ir.model'].search([('model', '=', 'wika.payment.request')], limit=1)
        model_wika_id = self.env['wika.approval.setting'].search([('model_id', '=', model_id.id)], limit=1)
        user = self.env['res.users'].search([('branch_id', '=', self.branch_id.id)])
        groups_id = None

        if model_wika_id:
            groups_line = self.env['wika.approval.setting.line'].search([
                ('branch_id', '=', self.branch_id.id),
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', model_wika_id.id)
            ], limit=1)
            groups_id = groups_line.groups_id

        if groups_id:
            for x in groups_id.users:
                activity_ids = self.env['mail.activity'].create({
                        'activity_type_id': 4,
                        'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'wika.payment.request')], limit=1).id,
                        'res_id': self.id,
                        'user_id': x.id,
                        'summary': """ Need Approval Document PO """
                    })
            for record in self:
                if any(not line.document for line in record.document_ids):
                    raise ValidationError('Document belum di unggah, mohon unggah file terlebih dahulu!')
        
    def action_request(self):
        self.write({'state': 'request'})

    def action_approve(self):
        user = self.env['res.users'].search([('id','=',self._uid)], limit=1)
        cek = False
        model_id = self.env['ir.model'].search([('model','=', 'wika.payment.request')], limit=1)
        if model_id:
            # print ("TESTTTTTTTTTTTTTTT", model_id)
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
                self.state = 'approve'
            else:
                self.step_approve += 1

            for invoice_id in self.invoice_ids.ids:
                invoice = self.env['account.move'].browse(invoice_id)
                pr_id = self.env['wika.payment.request'].search([('id', '=', self.id)], limit=1)
                invoice.write({'pr_id': pr_id.id}) 

            audit_log_obj = self.env['wika.pr.approval.line'].create({'user_id': self._uid,
                'groups_id' :groups_id.id,
                'date': datetime.now(),
                'note': 'Approve',
                'pr_id': self.id
                })
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def action_cancel(self):
        self.write({'state': 'draft'})

    def action_reject(self):
        action = self.env.ref('wika_payment_request.action_reject_pr_wizard').read()[0]
        return action

    def unlink(self):
        for record in self:
            if record.state in ('request', 'approve'):
                raise ValidationError('Tidak dapat menghapus ketika status Payment Request dalam keadaan Request atau Approve')
        return super(WikaPaymentRequest, self).unlink()

class WikaPrDocumentLine(models.Model):
    _name = 'wika.pr.document.line'
    _description = 'PR Document Line'

    pr_id = fields.Many2one('wika.payment.request', string='pr id')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(string="Upload File", attachment=True, store=True)
    filename = fields.Char(string="File Name")
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verif', 'Verif'),
    ], string='Status', default='waiting')
    
    @api.depends('document')
    def _compute_state(self):
        for rec in self:
            if rec.document:
                rec.state = 'uploaded'

    @api.onchange('document')
    def _onchange_document(self):
        if self.document:
            self.state = 'uploaded'

    @api.constrains('document', 'filename')
    def _check_attachment_format(self):
        for record in self:
            if record.filename and not record.filename.lower().endswith('.pdf'):
                raise ValidationError('Tidak dapat mengunggah file selain berformat PDF!')
            
class WikaPrApprovalLine(models.Model):
    _name = 'wika.pr.approval.line'
    _description = 'Wika Approval Line'

    pr_id = fields.Many2one('wika.payment.request', string='pr id')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')