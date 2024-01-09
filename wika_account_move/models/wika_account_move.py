from odoo import fields, models, api
from odoo.exceptions import AccessError, ValidationError
from datetime import datetime

class WikaInheritedAccountMove(models.Model):
    _inherit = 'account.move'
    
    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='BAP')
    branch_id = fields.Many2one('res.branch', string='Divisi')
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    document_ids = fields.One2many('wika.invoice.document.line', 'invoice_id', string='Document Line')
    history_approval_ids = fields.One2many('wika.invoice.approval.line', 'invoice_id', string='History Approval Line')
    reject_reason_account = fields.Text(string='Reject Reason')
    step_approve = fields.Integer(string='Step Approve')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('upload', 'Upload'),
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
            ('reject', 'Reject'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )

    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)

    def action_submit(self):
        self.write({'state': 'upload'})
        self.step_approve += 1
        model_id = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
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
            activity_ids = self.env['mail.activity'].create({
                    'activity_type_id': 4,
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1).id,
                    'res_id': self.id,
                    'user_id': x.id,
                    'summary': """ Need Approval Document PO """
                })
    
    def action_approve(self):
        user = self.env['res.users'].search([('id','=',self._uid)], limit=1)
        print("TESTTTTTTTTTTTTTT", user)
        cek = False
        model_id = self.env['ir.model'].search([('model','=', 'account.move')], limit=1)
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
                self.state = 'approve'
            else:
                self.step_approve += 1

            self.env['wika.invoice.approval.line'].create({'user_id': self._uid,
                'groups_id' :groups_id.id,
                'date': datetime.now(),
                'note': 'Approve',
                'invoice_id': self.id
                })
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def action_reject(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        cek = False
        model_id = self.env['ir.model'].search([('model','=', 'account.move')], limit=1)
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
                'res_model': "reject.wizard.account.move",
                'view_type': "form",
                'target': 'new',
                'view_mode': "form",
                'context': {'groups_id': groups_id.id},
                'view_id': self.env.ref('wika_account_move.reject_wizard_form').id,
            }
            return action
        else:
            raise ValidationError('User Akses Anda tidak berhak Reject!')

    @api.onchange('partner_id')
    def _onchange_(self):
        if self.partner_id:
            model_model = self.env['ir.model'].sudo()
            document_setting_model = self.env['wika.document.setting'].sudo()
            model_id = model_model.search([('model', '=', 'account.move')], limit=1)
            print("partner_id----------TEST--------", model_id)
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

            if doc_setting_id:
                self.document_ids.unlink()

                document_list = []
                for document_line in doc_setting_id:
                    document_list.append((0, 0, {
                        'invoice_id': self.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                self.document_ids = document_list
            else:
                raise AccessError("Data dokumen tidak ada!")

class WikaInvoiceDocumentLine(models.Model):
    _name = 'wika.invoice.document.line'
    _description = 'Invoice Document Line'

    invoice_id = fields.Many2one('account.move', string='Invoice id')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(string="Upload File", attachment=True, store=True)
    filename = fields.Char(string="File Name")
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verif', 'Verif'),
    ], string='Status', default='waiting')

class WikaInvoiceApprovalLine(models.Model):
    _name = 'wika.invoice.approval.line'
    _description = 'Wika Approval Line'

    invoice_id = fields.Many2one('account.move', string='Invoice id')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')