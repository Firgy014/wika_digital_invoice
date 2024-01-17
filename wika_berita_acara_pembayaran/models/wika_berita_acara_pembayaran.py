from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, Warning, AccessError

class WikaBeritaAcaraPembayaran(models.Model):
    _name = 'wika.berita.acara.pembayaran'
    _description = 'Berita Acara Pembayaran'
    _inherit = ['mail.thread']

    name = fields.Char(string='Nomor BAP', readonly=True, default='/')
    branch_id = fields.Many2one('res.branch', string='Divisi')
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    po_id = fields.Many2one('purchase.order', string='Nomor PO', domain="[('state', '=', 'purchase')]")
    partner_id = fields.Many2one('res.partner', string='Vendor')
    bap_ids = fields.One2many('wika.berita.acara.pembayaran.line', 'bap_id', string='List BAP')
    document_ids = fields.One2many('wika.bap.document.line', 'bap_id', string='List Document')
    history_approval_ids = fields.One2many('wika.bap.approval.line', 'bap_id', string='List Approval')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    state = fields.Selection([('draft', 'Draft'), ('upload', 'Upload'), ('approve', 'Approve'), ('reject', 'Reject')], string='Status', readonly=True, default='draft')
    reject_reason = fields.Text(string='Reject Reason')
    step_approve = fields.Integer(string='step approve')
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)

    @api.onchange('partner_id')
    def _onchange_(self):
        if self.partner_id:
            model_model = self.env['ir.model'].sudo()
            document_setting_model = self.env['wika.document.setting'].sudo()
            model_id = model_model.search([('model', '=', 'wika.berita.acara.pembayaran')], limit=1)
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

            if doc_setting_id:
                self.document_ids.unlink()

                document_list = []
                for document_line in doc_setting_id:
                    document_list.append((0, 0, {
                        'bap_id': self.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                self.document_ids = document_list
            else:
                raise AccessError("Data dokumen tidak ada!")
            # print("partner_id-----------", model_id)

    def action_reject(self):
        action = self.env.ref('wika_berita_acara_pembayaran.action_reject_wizard').read()[0]

        return action

    def action_submit(self):
        self.write({'state': 'upload'})
        self.step_approve += 1
        model_id = self.env['ir.model'].search([('model', '=', 'wika.berita.acara.pembayaran')], limit=1)
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
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'wika.berita.acara.pembayaran')], limit=1).id,
                    'res_id': self.id,
                    'user_id': x.id,
                    'summary': """ Need Approval Document PO """
                })

    def action_approve(self):
        user = self.env['res.users'].search([('id','=',self._uid)], limit=1)
        documents_model = self.env['documents.document'].sudo()
        cek = False
        model_id = self.env['ir.model'].search([('model','=', 'wika.berita.acara.pembayaran')], limit=1)
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
                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'BAP')], limit=1)
                # print("TESTTTTTTTTTTTTTTTTTTTTT", folder_id)
                if folder_id:
                    facet_id = self.env['documents.facet'].sudo().search([
                        ('name', '=', 'Wika BAP'),
                        ('folder_id', '=', folder_id.id)
                    ], limit=1)
                    # print("TESTTTTTTTTTERRRRRRR", facet_id)
                    for doc in self.document_ids.filtered(lambda x: x.state == 'uploaded'):
                        doc.state = 'verif'
                        attachment_id = self.env['ir.attachment'].sudo().create({
                            'name': doc.filename,
                            'datas': doc.document,
                            'res_model': 'documents.document',
                        })
                        # print("SSSIIIIUUUUUUUUUUUUUUUUUU", attachment_id)
                        if attachment_id:
                            documents_model.create({
                                'attachment_id': attachment_id.id,
                                'folder_id': folder_id.id,
                                'tag_ids': facet_id.tag_ids.ids,
                                # 'partner_id': doc.purchase_id.partner_id.id,
                            })
            else:
                self.step_approve += 1

            audit_log_obj = self.env['wika.bap.approval.line'].create({'user_id': self._uid,
                'groups_id' :groups_id.id,
                'datetime': datetime.now(),
                'note': 'Approve',
                'bap_id': self.id
                })
        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')
            
    def action_cancel(self):
        self.write({'state': 'draft'})
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('wika.berita.acara.pembayaran')
        return super(WikaBeritaAcaraPembayaran, self).create(vals)

    @api.onchange('po_id')
    def onchange_po(self):
        self.partner_id = self.po_id.partner_id.id

class WikaBeritaAcaraPembayaranLine(models.Model):
    _name = 'wika.berita.acara.pembayaran.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    picking_id = fields.Many2one('stock.picking', string='NO GR/SES')
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Integer(string='Quantity')
    tax_ids = fields.Many2many('account.tax', string='Tax')
    currency_id = fields.Many2one('res.currency', string='Currency')
    unit_price = fields.Monetary(string='Unit Price')
    sub_total = fields.Monetary(string='Subtotal' , compute= 'compute_sub_total')
    
    @api.depends('qty', 'unit_price')
    def compute_sub_total(self):
        for record in self:
            record.sub_total = record.qty * record.unit_price

class WikaBabDocumentLine(models.Model):
    _name = 'wika.bap.document.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
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
            
class WikaBabApprovalLine(models.Model):
    _name = 'wika.bap.approval.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    datetime = fields.Datetime('Date')
    note = fields.Char('Note')
