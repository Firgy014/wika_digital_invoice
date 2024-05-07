from odoo import models, fields, api,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning, AccessError
import random
import string
import requests
import json
import logging
_logger = logging.getLogger(__name__)
class WikaPaymentRequest(models.Model):
    _name = 'wika.payment.request'
    _description = 'Wika Payment Request'
    _inherit = ['mail.thread']

    wika_pr_lines = fields.One2many('wika.payment.request.line', 'pr_id', string='Payment Request Lines')

    @api.onchange('type_payment')
    def _onchange_type_payment(self):
        self.invoice_ids = False

    @api.model
    def default_get(self, fields):
        res = super(WikaPaymentRequest, self).default_get(fields)
        res['invoice_ids'] = False
        return res

    @api.onchange('invoice_ids')
    def _onchange_invoice_ids(self):
        for rec in self:
            used_partial_ids = self.env['wika.payment.request.line'].search([('pr_id', '!=', self.id)]).mapped('partial_id.id')
            existing_invoices = rec.move_ids.mapped('invoice_id.id')
            move_lines = []
            for invoice in rec.invoice_ids:
                if invoice.id not in existing_invoices:
                    for partial in invoice.partial_request_ids.filtered(lambda p: not p.is_already_pr):
                        if partial.id not in used_partial_ids:
                            move_lines.append((0, 0, {
                                'invoice_id': invoice.id,
                                'partial_id': partial.id,
                                'partner_id': invoice.partner_id.id,
                                'branch_id': invoice.branch_id.id,
                                'project_id': invoice.project_id.id,
                                'amount': partial.partial_amount,
                            }))
            # Remove existing move lines that are not in the current invoice_ids
            move_lines_ids = [move_id.id for move_id in rec.move_ids if move_id.invoice_id.id in existing_invoices]
            rec.move_ids = [(3, move_id_id) for move_id_id in move_lines_ids] + move_lines


    def write(self, vals):
        res = super(WikaPaymentRequest, self).write(vals)
        if 'invoice_ids' in vals:
            for record in self:
                lines_to_delete = record.move_ids.filtered(lambda x: x.invoice_id.id not in record.invoice_ids.ids)
                lines_to_delete.unlink()
        return res

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
        ('verified', 'Verified'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ], readonly=True, string='status', default='draft')
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True,default=_getdefault_branch)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project', required=True,default=_getdefault_project)
    invoice_ids = fields.Many2many(
        'account.move',
        string='Invoice',
        required=True,
        domain="[('state', '=', 'approved'), ('status_payment', '=', 'Not Request'), '|', ('partial_request_ids', '=', False), ('partial_request_ids', '=', None)]"
    )
    move_ids = fields.One2many(
        comodel_name="wika.payment.request.line",
        string="Account Moves",
        inverse_name='pr_id',
    )
    history_approval_ids = fields.One2many('wika.pr.approval.line', 'pr_id', string='Approval Line')
    total = fields.Integer(string='Total', compute='compute_total')
    step_approve = fields.Integer(string='Step Approve',default=1)
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
    activity_summary = fields.Char(string='Activity Summary')
    activity_user_id= fields.Many2one(comodel_name='res.users',string='Assign User')
    approval_stage = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat'),
    ], string='Status Position')
    approval_line_id= fields.Many2one(comodel_name='wika.approval.setting.line')
    is_posted_to_sap = fields.Boolean(string='Posted to SAP', default=False)
    partial_payment_ids = fields.Many2many('wika.partial.payment.request', string='Partial',
        domain="[('state', '=', 'approved'), ('payment_state', '=', 'not request')]")

    @api.onchange('partial_payment_ids')
    def _check_partial_payment_ids(self):
        if len(self.partial_payment_ids) > 1:
            raise UserError("Anda hanya boleh memilih satu baris partial payment.")

    @api.model
    def _getdefault_branch(self):
        user_obj = self.env['res.users']
        branch_id = user_obj.browse(self.env.user.id).branch_id or False
        if branch_id:
            branch_id=branch_id.id
        return branch_id
    #
    # @api.onchange('invoice_ids')
    # def _onchange_invoice_ids(self):
    #     move_lines = []
    #     for invoice in self.invoice_ids:
    #         print ("emang masuk sini ga sih")
    #         move_lines.append((0, 0, {
    #             'invoice_id': invoice.id,
    #             'partner_id': invoice.partner_id.id,
    #             'branch_id': invoice.branch_id.id,
    #             'project_id': invoice.project_id.id,
    #             'department_id': invoice.department_id.id,
    #             'amount':invoice.total_partial_pr,
    #             'is_partial_pr':invoice.is_partial_pr
    #
    #         }))
    #     self.move_ids = move_lines

    # @api.onchange('invoice_ids','state')
    # def _onchange_invoice_ids_delete(self):
    #     if self.state !='draft':
    #         for move_line in self.move_ids:
    #             if move_line.invoice_id not in self.invoice_ids:
    #                 move_line.unlink()

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

    def assign_requested(self):
        model_model = self.env['ir.model'].sudo()
        model_id = model_model.search([('model', '=', 'wika.payment.request')], limit=1)
        for res in self:
            level=res.level
            first_user = False
            if level:
                approval_id = self.env['wika.approval.setting'].sudo().search(
                    [ ('model_id', '=', model_id.id),('transaction_type', '=', 'pr'),('level', '=', level)], limit=1)
                approval_line_id = self.env['wika.approval.setting.line'].search([
                    ('sequence', '=', 2),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                print(approval_line_id)
                groups_id = approval_line_id.groups_id
                if groups_id:
                    for x in groups_id.users:
                        if level == 'Proyek' and self.project_id in x.project_ids:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == res.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == res.department_id:
                            first_user = x.id
                if first_user:
                    activity=self.env['mail.activity'].sudo().create({
                        'activity_type_id': 4,
                        'res_model_id': model_id.id,
                        'res_id': res.id,
                        'user_id': first_user,
                        # 'nomor_po': res.po_id.name,
                        'date_deadline': fields.Date.today() + timedelta(days=2),
                        'state': 'planned',
                        'summary': f"Need Verified Doc"
                    })
                    res.approval_stage=level
                    res.activity_user_id=activity.user_id.id
                    res.activity_summary=activity.summary
                    res.approval_line_id=approval_line_id.id
                    self.env['wika.pr.approval.line'].create({'user_id': self._uid,
                                                              # 'groups_id': groups_id.id,
                                                              'date': datetime.now(),
                                                              'note': 'Request Payment',
                                                              'pr_id': self.id
                                                              })

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('wika.payment.request')
        #res.assign_todo_first()
        return super(WikaPaymentRequest, self).create(vals)

    @api.depends('move_ids')
    def compute_total(self):
        for record in self:
            total_amount = sum(record.move_ids.mapped('amount'))
            record.total = total_amount

    def action_submit(self):
        for record in self:
            if any(line.state != 'verified' for line in record.invoice_ids.document_ids):
                raise ValidationError('Document belum verified, silahkan cek terlebih dahulu!')
        for x in self.move_ids:
            x.write({'state':'request','nomor_payment_request':self.name,'payment_request_date':self.date,'payment_method':self.payment_method})
        self.write({'state': 'request'})
        for invoice in self.invoice_ids:
            invoice.write({'status_payment': 'Request Proyek'})
        for partial_payment in self.partial_payment_ids:
            partial_payment.write({'payment_state': 'requested'})
        self.step_approve += 1
        self.assign_requested()

    def action_approve(self):
        if self.activity_user_id.id ==self._uid:
            move_lines = []
            for partial in self.partial_payment_ids:
                move_lines.append((0, 0, {
                    'invoice_id': partial.invoice_id.id,
                    'partial_id': partial.id,
                    'partner_id': partial.invoice_id.partner_id.id,
                    'branch_id': partial.invoice_id.branch_id.id,
                    'project_id': partial.invoice_id.project_id.id,
                    'amount': partial.partial_amount,
                }))

            self.move_ids = move_lines

            approval_id=self.approval_line_id.approval_id
            step_approve=self.approval_line_id.sequence+1
            apploval_line_next_id=self.env['wika.approval.setting.line'].sudo().search(
                        [('approval_id', '=', approval_id.id),('sequence','=',step_approve)], limit=1)
            groups_id_next = apploval_line_next_id.groups_id
            first_user=False
            if groups_id_next:
                print (groups_id_next.name)
                for x in groups_id_next.users:
                    if self.level == 'Proyek' and x.branch_id == self.branch_id:
                        first_user = x.id
                    if self.level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                        first_user = x.id
                    if self.level == 'Divisi Fungsi' and x.department_id == self.department_id:
                        first_user = x.id
                if first_user:
                    for invoice in self.invoice_ids:
                        print (invoice)
                        invoice.write({'status_payment': 'Request Divisi',
                                       'payment_block':'C'})
                        self.env['wika.payment.request.line'].sudo().create({
                            'pr_id':self.id,
                            'invoice_id': invoice.id,
                            'partner_id': invoice.partner_id.id,
                            'branch_id': invoice.branch_id.id,
                            'project_id': invoice.project_id.id,
                            'department_id': invoice.department_id.id,
                            'amount': invoice.total_partial_pr,
                            'is_partial_pr': invoice.is_partial_pr,
                            'payment_method': self.payment_method,
                            'payment_request_date': self.date,
                            'approval_line_id':apploval_line_next_id.id,
                            'next_user_id':first_user
                        })
                    audit_log_obj = self.env['wika.pr.approval.line'].create({'user_id': self._uid,
                        'groups_id' :self.approval_line_id.groups_id.id,
                        'date': datetime.now(),
                        'note': 'Verified',
                        'pr_id': self.id
                        })
                    self.write({'state': 'verified','activity_summary':'Request Divisi','approval_stage':'Divisi Operasi'})
                    self.sudo().send_proyek_approved_pr_to_sap()
                else:
                    raise ValidationError('User Next Approval tidak ditemukan!')

        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    # def action_approve(self):
    #     if self.activity_user_id.id == self._uid:
    #         move_lines = []
    #         approval_id = self.approval_line_id.approval_id
    #         step_approve = self.approval_line_id.sequence + 1
    #         apploval_line_next_id = self.env['wika.approval.setting.line'].sudo().search(
    #             [('approval_id', '=', approval_id.id), ('sequence', '=', step_approve)], limit=1)
    #         groups_id_next = apploval_line_next_id.groups_id
    #         first_user = False
    #         if groups_id_next:
    #             print(groups_id_next.name)
    #             for x in groups_id_next.users:
    #                 if self.level == 'Proyek' and x.branch_id == self.branch_id:
    #                     first_user = x.id
    #                 if self.level == 'Divisi Operasi' and x.branch_id == self.branch_id:
    #                     first_user = x.id
    #                 if self.level == 'Divisi Fungsi' and x.department_id == self.department_id:
    #                     first_user = x.id
    #             if first_user:
    #                 for invoice in self.invoice_ids:
    #                     print(invoice)
    #                     invoice.write({'status_payment': 'Request Divisi', 'payment_block': 'C'})
    #                     move_lines.append((0, 0, {
    #                         'invoice_id': invoice.id,
    #                         'partial_id': partial.id,
    #                         'partner_id': invoice.partner_id.id,
    #                         'branch_id': invoice.branch_id.id,
    #                         'project_id': invoice.project_id.id,
    #                         'amount': invoice.total_partial_pr,
    #                     }))
    #                 self.move_ids = move_lines  # Mengisi move_ids di model 'wika.payment.request'
    #                 audit_log_obj = self.env['wika.pr.approval.line'].create({'user_id': self._uid,
    #                     'groups_id': self.approval_line_id.groups_id.id,
    #                     'date': datetime.now(),
    #                     'note': 'Verified',
    #                     'pr_id': self.id
    #                     })
    #                 self.write({'state': 'verified', 'activity_summary': 'Request Divisi', 'approval_stage': 'Divisi Operasi'})
    #                 # self.send_proyek_approved_pr_to_sap()
    #             else:
    #                 raise ValidationError('User Next Approval tidak ditemukan!')
    #     else:
    #         raise ValidationError('User Akses Anda tidak berhak Approve!')

    def action_reject(self):
        action = self.env.ref('wika_payment_request.action_reject_pr_wizard').read()[0]
        return action

    def unlink(self):
        for record in self:
            if record.state in ('request', 'approve'):
                raise ValidationError('Tidak dapat menghapus ketika status Payment Request dalam keadaan Request atau Approve')
        return super(WikaPaymentRequest, self).unlink()
    
    def _generate_random_string(self):
        length = 32
        letters_and_digits = string.ascii_uppercase + string.digits
        random_string = ''.join((random.choice(letters_and_digits) for i in range(length)))

        return random_string

    def send_proyek_approved_pr_to_sap(self):
        print("masukkk_____proyek")
        _logger.info("API PROYEKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK")
        package_id = self._generate_random_string()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        url_config = self.env['wika.integration'].search([('name', '=', 'URL Payment Request Proyek')], limit=1)

        auth = ('WIKA_INT', 'Initial123')
        url = url_config.url
        headers = {'x-csrf-token': 'fetch'}
        # GET Req
        response = requests.get(url, headers=headers, auth=auth)
        fetched_token = response.headers.get('x-csrf-token')
        fetched_cookies = response.cookies.get_dict()
        invoice_list = []
        data_ref = {}
        for invoice in self.invoice_ids:
            data_ref = {
                'BELNR': invoice.payment_reference,
                'GJAHR': str(invoice.date)[:4],
                'ZLSPR': invoice.payment_block,
                'XREF3': invoice.project_id.sap_code
            }
            invoice_list.append(data_ref)

        payload = json.dumps({
            "DEVID": "YFII016",
            "PACKAGEID": package_id,
            "COCODE": "A000",
            "PRCTR": "",
            "TIMESTAMP": timestamp,
            "DATA": invoice_list
        })
        print (payload)
        # POST Req
        post_headers = {
            'x-csrf-token': fetched_token,
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw=='
        }
        response_post = requests.request("POST", url, headers=post_headers, data=payload, cookies=fetched_cookies)

        # Loop melalui setiap objek dalam daftar respons

        #parsed_response = json.loads(response_post.text)
        # message = parsed_response[0]["MESSAGE"]
        # print(message)
        self.is_posted_to_sap = True


class WikaPrApprovalLine(models.Model):
    _name = 'wika.pr.approval.line'
    _description = 'Wika Approval Line'

    pr_id = fields.Many2one('wika.payment.request', string='pr id')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')

class WikaPrLine(models.Model):
    _name = 'wika.payment.request.line'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Wika Payment Request Line'

    pr_id = fields.Many2one('wika.payment.request', string='No Payment Request')
    partial_id = fields.Many2one('wika.partial.payment.request', string='No Partial')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    branch_id = fields.Many2one('res.branch',string='Divisi')
    project_id = fields.Many2one('project.project',string='Project')
    department_id = fields.Many2one('res.branch',string='Department')
    amount=fields.Float(string='Amount Request')
    is_partial_pr=fields.Boolean(string='Partial Payment Request',default=False)
    payment_block = fields.Selection([
        ('B', 'Default Invoice'),
        ('C', 'Pengajuan Ke Divisi'),
        ('D', 'Pengajuan Ke Pusat'),
        ('" "', 'Free For Payment (Sudah Approve)'),
        ('K', 'Dokumen Kembali'),
    ], string='Payment Block', default='B')
    payment_method = fields.Selection([
        ('transfer tunai', 'Transfer Tunai (TT)'),
        ('fasilitas', 'Fasilitas'),
    ], string='Payment Method')
    payment_request_date= fields.Date(string='Payment Request Date')
    nomor_payment_request= fields.Char(string='Nomor Payment Request')
    level=fields.Selection(related='pr_id.level')
    check_biro = fields.Boolean(related='pr_id.check_biro')
    step_approve = fields.Integer(string='Step Approve')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Requested'),
        ('verified', 'Verified'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ], readonly=True, string='status',default='draft')
    next_user_id= fields.Many2one(comodel_name='res.users',string='Assign User')
    approval_stage = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat'),
    ], string='Position')
    approval_line_id= fields.Many2one(comodel_name='wika.approval.setting.line')
    is_already_pr = fields.Boolean(string='Already PR', default=False)

    @api.model
    def create(self, values):
        line = super(WikaPrLine, self).create(values)
        # Update is_already_pr in partial.payment.request
        if line.partial_id:
            line.partial_id.write({'is_already_pr': True})
        return line

    def write(self, values):
        result = super(WikaPrLine, self).write(values)
        # Update is_already_pr in partial.payment.request
        if 'partial_id' in values:
            for line in self:
                if line.partial_id:
                    line.partial_id.write({'is_already_pr': True})
        return result

    def unlink(self):
        partial_ids = self.mapped('partial_id')
        result = super(WikaPrLine, self).unlink()
        # Update is_already_pr in partial.payment.request
        for partial in partial_ids:
            if not self.search([('partial_id', '=', partial.id)]):
                partial.write({'is_already_pr': False})
        return result

    def action_approve(self):
        if self.next_user_id.id ==self._uid:
            move_lines = []
            approval_id=self.approval_line_id.approval_id
            step_approve=self.approval_line_id.sequence+1
            apploval_line_next_id=self.env['wika.approval.setting.line'].sudo().search(
                        [('approval_id', '=', approval_id.id),('sequence','=',step_approve)], limit=1)
            groups_id_next = apploval_line_next_id.groups_id
            first_user=False
            if groups_id_next:
                for x in groups_id_next.users:
                    if self.level == 'Proyek' and x.branch_id == self.branch_id or x.branch_id.parent_id.code == 'Pusat':
                        first_user = x.id
                    if self.level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                        first_user = x.id
                    if self.level == 'Divisi Fungsi' and x.department_id == self.department_id:
                        first_user = x.id
                    print (first_user)
                if first_user:
                    self.write({'next_user_id': first_user, 'approval_line_id': apploval_line_next_id})
                    if apploval_line_next_id.level_role=='Divisi Operasi':
                        self.pr_id.write({'activity_summary': 'Request Divisi','approval_stage':'Divisi Operasi'})
                    elif apploval_line_next_id.level_role == 'Pusat':
                        self.pr_id.write({ 'activity_summary': 'Request Pusat','approval_stage':'Pusat'})
                        self.invoice_id.write({'status_payment': 'Request Pusat','payment_block':'D'})
                        self.sudo().send_divisi_approved_pr_to_sap()

                    # audit_log_obj = self.env['wika.pr.approval.line'].create({'user_id': self._uid,
                    #         'groups_id' :self.approval_line_id.groups_id.id,
                    #         'date': datetime.now(),
                    #         'note': 'Verified',
                    #         'pr_id': self.id
                    #         })
                else:
                    raise ValidationError('User Next Approval tidak ditemukan!')
            else:
                self.sudo().send_pusat_approved_pr_to_sap()
                self.pr_id.write({'state': 'approve'})
                self.write({'next_user_id': False})
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def _generate_random_string(self):
        length = 32
        letters_and_digits = string.ascii_uppercase + string.digits
        random_string = ''.join((random.choice(letters_and_digits) for i in range(length)))

        return random_string

    def send_divisi_approved_pr_to_sap(self):
        package_id = self._generate_random_string()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        auth = ('WIKA_INT', 'Initial123')
        url_config = self.env['wika.integration'].search([('name', '=', 'URL Payment Request Divisi')], limit=1)

        url = url_config.url
        headers = {'x-csrf-token': 'fetch'}

        # GET Req
        response = requests.get(url, headers=headers, auth=auth)
        fetched_token = response.headers.get('x-csrf-token')
        fetched_cookies = response.cookies.get_dict()

        invoice_list = []
        data_ref = {}
        data_ref = {
            'BELNR': self.invoice_id.payment_reference,
            'GJAHR': str(self.invoice_id.date)[:4],
            'ZLSPR': 'D',
            'ZUONR': self.invoice_id.project_id.sap_code
        }
        invoice_list.append(data_ref)
        payload = json.dumps({
            "DEVID": "YFII016A",
            "PACKAGEID": package_id,
            "COCODE": "A000",
            "PRCTR": "",
            "TIMESTAMP": timestamp,
            "DATA": invoice_list
        })
        # POST Req
        post_headers = {
            'x-csrf-token': fetched_token,
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw=='
        }
        response_post = requests.request("POST", url, headers=post_headers, data=payload, cookies=fetched_cookies)
        parsed_response = json.loads(response_post.text)
        message = parsed_response[0]["MESSAGE"]
        self.invoice_id.msg_sap=message
        _logger.info(response_post.text)
        self.pr_id.is_posted_to_sap = True

    def send_pusat_approved_pr_to_sap(self):
        package_id = self._generate_random_string()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.invoice_id.write({'status_payment': 'Ready To Pay', 'payment_block': ""})

        auth = ('WIKA_INT', 'Initial123')
        url_config = self.env['wika.integration'].search([('name', '=', 'URL Payment Request Pusat')], limit=1)

        url = url_config.url
        headers = {'x-csrf-token': 'fetch'}

        # GET Req
        response = requests.get(url, headers=headers, auth=auth)
        fetched_token = response.headers.get('x-csrf-token')
        fetched_cookies = response.cookies.get_dict()

        invoice_list = []
        data_ref = {}

        data_ref = {
            'BELNR': self.invoice_id.payment_reference,
            'GJAHR': str(self.invoice_id.date)[:4],
            'ZLSPR': "",
            'ZLSCH': "F"
        }
        invoice_list.append(data_ref)

        payload = json.dumps({
            "DEVID": "YFII016B",
            "PACKAGEID": package_id,
            "COCODE": "A000",
            "PRCTR": "",
            "TIMESTAMP": timestamp,
            "DATA": invoice_list
        })
        # POST Req
        post_headers = {
            'x-csrf-token': fetched_token,
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw=='
        }
        response_post = requests.request("POST", url, headers=post_headers, data=payload, cookies=fetched_cookies)
        _logger.info(response_post.text)
        parsed_response = json.loads(response_post.text)
        message = parsed_response[0]["MESSAGE"]
        self.invoice_id.msg_sap=message
        self.pr_id.is_posted_to_sap = True
