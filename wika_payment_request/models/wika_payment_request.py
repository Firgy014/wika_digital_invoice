from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning


class WikaPaymentRequest(models.Model):
    _name = 'wika.payment.request'
    _description = 'Wika Payment Request'

    name = fields.Char(string='Nomor Payment Request', readonly=True ,default='/')
    date = fields.Date(string='Tanggal Payement Request')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('upload', 'upload'),
        ('request', 'Request'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], readonly=True, string='status', default='draft')
    branch_id = fields.Many2one('res.branch', string='Divisi')
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    invoice_ids = fields.Many2many('account.move', string='Invoice')
    document_ids = fields.One2many('wika.pr.document.line', 'pr_id', string='Document Line')
    history_approval_ids = fields.One2many('wika.pr.approval.line', 'pr_id', string='Approval Line')
    total = fields.Integer(string='Total', compute='compute_total')
    step_approve = fields.Integer(string='Step Approve')
    reject_reason_pr = fields.Text(string='Reject Reason')
    # invoice_ids = fields.Many2many(
    #     'account.move',  # Ganti dengan nama model invoice line yang sesuai
    #     'pr_id',
    #     domain="[('pr_id', '=', False), ('move_type', '=', 'in_invoice')]"
    #     # Ganti 'your.invoice.line.model' dengan nama model invoice line yang sesuai
    # )
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
        if any (doc.state != 'verif'  for doc in self.document_ids):
            raise UserError('Tidak bisa submit karena ada dokumen yang belum diverifikasi!')
        self.write({'state': 'upload'})
        self.step_approve += 1
        
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
            
class WikaPrApprovalLine(models.Model):
    _name = 'wika.pr.approval.line'
    _description = 'Wika Approval Line'

    pr_id = fields.Many2one('wika.payment.request', string='pr id')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')