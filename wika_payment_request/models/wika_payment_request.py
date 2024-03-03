from odoo import models, fields, api,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning, AccessError


class WikaPaymentRequest(models.Model):
    _name = 'wika.payment.request'
    _description = 'Wika Payment Request'
    _inherit = ['mail.thread']

    @api.model
    def _getdefault_branch(self):
        user_obj = self.env['res.users']
        branch_id = user_obj.browse(self.env.user.id).branch_id or False
        project_id = user_obj.browse(self.env.user.id).project_id or False
        if branch_id and not project_id:
            branch_id=branch_id.id
        elif project_id and not branch_id:
            branch_id=project_id.branch_id.id
        return branch_id

    @api.model
    def _getdefault_project(self):
        user_obj = self.env['res.users']
        project_id = user_obj.browse(self.env.user.id).project_id or False
        if project_id:
            project_id=project_id.id
        return project_id

    name = fields.Char(string='Nomor Payment Request', readonly=True ,default='/')
    date = fields.Date(string='Tanggal Payment Request', required=True, default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Requested'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ], readonly=True, string='status', default='draft')
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True,default=_getdefault_branch)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project', required=True,default=_getdefault_project)
    invoice_ids = fields.Many2many('account.move', string='Invoice', required=True)
    #invoice_ids = fields.One2many('wika.payment.request.line', string='Invoice', required=True)

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

    @api.model
    def _getdefault_branch(self):
        user_obj = self.env['res.users']
        branch_id = user_obj.browse(self.env.user.id).branch_id or False
        if branch_id:
            branch_id=branch_id.id
        return branch_id

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
            total_amount = sum(record.invoice_ids.mapped('amount_sisa_pr'))
            record.total = total_amount

    def action_submit(self):
        self.write({'state': 'request'})
        self.step_approve += 1
        if self.level=='Proyek':
            for x in self.invoice_ids:
                x.write({'payment_block': 'C'})
        if self.level == 'Divisi Operasi':
            for x in self.invoice_ids:
                x.write({'payment_block': 'C'})
        # model_id = self.env['ir.model'].search([('model', '=', 'wika.payment.request')], limit=1)
        # groups_id = None
        # level = self.level
        # if level:
        #     approval_id = self.env['wika.approval.setting'].sudo().search(
        #         [('model_id', '=', model_id.id), ('level', '=', level), ('transaction_type', '=', 'pr')], limit=1)
        #     approval_line_id = self.env['wika.approval.setting.line'].search([
        #         ('sequence', '=', 1),
        #         ('approval_id', '=', approval_id.id)
        #     ], limit=1)
        #     groups_id = approval_line_id.groups_id
        #     if groups_id:
        #         for x in groups_id.users:
        #             if level == 'Proyek' and x.project_id == self.project_id:
        #                 first_user = x.id
        #             if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
        #                 first_user = x.id
        #             if level == 'Divisi Fungsi' and x.department_id == self.department_id:
        #                 first_user = x.id
        #
        # if groups_id:
        #     for x in groups_id.users:
        #         activity_ids = self.env['mail.activity'].create({
        #                 'activity_type_id': 4,
        #                 'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'wika.payment.request')], limit=1).id,
        #                 'res_id': self.id,
        #                 'user_id': x.id,
        #                 'summary': """ Need Approval Document PO """
        #             })

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



    def action_reject(self):
        action = self.env.ref('wika_payment_request.action_reject_pr_wizard').read()[0]
        return action

    def unlink(self):
        for record in self:
            if record.state in ('request', 'approve'):
                raise ValidationError('Tidak dapat menghapus ketika status Payment Request dalam keadaan Request atau Approve')
        return super(WikaPaymentRequest, self).unlink()

class WikaPrApprovalLine(models.Model):
    _name = 'wika.pr.approval.line'
    _description = 'Wika Approval Line'

    pr_id = fields.Many2one('wika.payment.request', string='pr id')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
#
# class WikaPrLine(models.Model):
#     _name = 'wika.payment.request.line'
#     _description = 'Wika Payment Request Line'
#
#     pr_id = fields.Many2one('wika.payment.request', string='pr id')
#     invoice_id = fields.Many2one('account.move', string='Invoice')
#     partner_id = fields.Many2one('res.partner', related='invoice_id.partner_id',string='Vendor')
#     branch_id = fields.Many2one('res.branch',related='invoice_id.branch_id',string='Divisi')
#     project_id = fields.Many2one('project.project',related='invoice_id.project_id',string='Project')
#     department_id = fields.Many2one('res.branch',related='invoice_id.department_id',string='Project')
#     amount=fields.Float(string='Amount Request')
#     is_partial_pr=fields.Boolean(string='Partial Payment Request',default=False)
