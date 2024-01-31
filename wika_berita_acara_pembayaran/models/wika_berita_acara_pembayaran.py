from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, Warning, AccessError

class WikaBeritaAcaraPembayaran(models.Model):
    _name = 'wika.berita.acara.pembayaran'
    _description = 'Berita Acara Pembayaran'
    _inherit = ['mail.thread']

    name = fields.Char(string='Nomor BAP', readonly=True, default='/')
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    po_id = fields.Many2one('purchase.order', string='Nomor PO', required=True, domain="[('state', '=', 'approved')]")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    bap_ids = fields.One2many('wika.berita.acara.pembayaran.line', 'bap_id', string='List BAP', required=True)
    document_ids = fields.One2many('wika.bap.document.line', 'bap_id', string='List Document')
    history_approval_ids = fields.One2many('wika.bap.approval.line', 'bap_id', string='List Approval')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    state = fields.Selection([
        ('draft', 'Draft'), 
        ('upload', 'Upload'), 
        ('approve', 'Approve'), 
        ('reject', 'Reject')], string='Status', readonly=True, default='draft')
    reject_reason = fields.Text(string='Reject Reason')
    step_approve = fields.Integer(string='step approve')
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)
    bap_date = fields.Date(string='Tanggal BAP', required=True)
    bap_type = fields.Selection([
        ('progress', 'Progress'),
        ('uang muka', 'Uang Muka'),], string='Jenis BAP', default='progress')
    price_cut_ids = fields.One2many('wika.bap.pricecut.line', 'po_id')
    signatory_name = fields.Char(string='Nama Penanda Tangan', related="po_id.signatory_name")
    position = fields.Char(string='Jabatan', related="po_id.position")
    address = fields.Char(string='Alamat', related="po_id.address")
    job = fields.Char(string='Pekerjaan', related="po_id.job")
    vendor_signatory_name = fields.Char(string='Nama Penanda Tangan Vendor', related="po_id.vendor_signatory_name")
    vendor_position = fields.Char(string='Jabatan Vendor', related="po_id.vendor_position")
    begin_date = fields.Date(string='Tgl Mulai Kontrak', required=True, related="po_id.begin_date")
    sap_doc_number = fields.Char(string='Nomor Kontrak', required=True, related="po_id.sap_doc_number")
    amount_total = fields.Monetary(string='Total', related="po_id.amount_total")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)

    # move_ids_without_package = fields.One2many(
    #     'stock.move', 'picking_id', string="Stock moves not in package", compute='_compute_move_without_package',
    #     inverse='_set_move_without_package', compute_sudo=True)
    # # move_line_ids = fields.One2many('stock.move', 'picking_id', string='Move Line')

    narration = fields.Html(string='Terms and Conditions', store=True, readonly=False,)
    tax_totals = fields.Char(string="Invoice Totals")

    # @api.onchange('po_id')
    # def _onchange_po_id(self):
    #     # Filter domain untuk bap_ids berdasarkan nilai po_id
    #     domain = [('product_id.purchase_id', '=', self.po_id.id)] if self.po_id else []
    #     return {'domain': {'bap_ids': domain}}

    # @api.onchange('po_id')
    # def onchange_po_id(self):
    #     for rec in self:
    #         if rec.po_id:
    #             for line in rec.bap_ids:
    #                 find_c = self.env["purchase.order.line"].search([('order_id', '=', rec.po_id.id), ('product_id', '=', line.product_id.id)])

    #                 if find_c:
    #                     return {'domain': {'bap_ids': [('product_id', '=', find_c.product_id.id)]}}
    #         return {'domain': {'bap_ids': []}}

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

        for record in self:
            if any(not line.document for line in record.document_ids):
                raise ValidationError('Document belum di unggah, mohon unggah file terlebih dahulu!')

    # @api.constrains('document_ids')
    # def _check_documents(self):
    #     for record in self:
    #         if any(not line.document for line in record.document_ids):
    #             raise ValidationError('Dokumen belum diunggah. Mohon unggah file terlebih dahulu sebelum melanjutkan.')

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
                                'partner_id': doc.bap_id.partner_id.id,
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

    def unlink(self):
        for record in self:
            if record.state in ('upload', 'approve'):
                raise ValidationError('Tidak dapat menghapus ketika status Berita Acara Pembayaran (BAP) dalam keadaan Upload atau Approve')
        return super(WikaBeritaAcaraPembayaran, self).unlink()

    def action_print_bap(self):
        return self.env.ref('wika_berita_acara_pembayaran.report_wika_berita_acara_pembayaran_action').report_action(self)

class WikaBeritaAcaraPembayaranLine(models.Model):
    _name = 'wika.berita.acara.pembayaran.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    picking_id = fields.Many2one('stock.move', string='NO GR/SES', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Integer(string='Quantity', required=True)
    tax_ids = fields.Many2many('account.tax', string='Tax', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    unit_price = fields.Monetary(string='Unit Price', required=True)
    sub_total = fields.Monetary(string='Subtotal' , compute= 'compute_sub_total')
    untaxed_amount = fields.Monetary('untaxed amount')

    @api.depends('qty', 'unit_price')
    def compute_sub_total(self):
        for record in self:
            record.sub_total = record.qty * record.unit_price

    @api.constrains('picking_id')
    def _check_picking_id(self):
        for record in self:
            if not record.picking_id:
                raise ValidationError('Field "NO GR/SES" harus diisi. Tidak boleh kosong!')

    @api.onchange('po_id')
    def _onchange_po_id(self):
        if self.po_id:
            # Filter domain untuk product_id berdasarkan nilai po_id
            return {'domain': {'product_id': [('purchase_order_id', '=', self.po_id.id)]}}
        else:
            # Reset domain jika po_id dihapus
            return {'domain': {'product_id': []}}

class WikaBabDocumentLine(models.Model):
    _name = 'wika.bap.document.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(string="Upload File", attachment=True, store=True, required=True)
    filename = fields.Char(string="File Name")
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verif', 'Verif'),
    ], string='Status', default='waiting')

    @api.onchange('document')
    def onchange_document(self):
        if self.document:
            self.state = 'uploaded'
    
    @api.constrains('document', 'filename')
    def _check_attachment_format(self):
        for record in self:
            if record.filename and not record.filename.lower().endswith('.pdf'):
                raise ValidationError('Tidak dapat mengunggah file selain berformat PDF!')

class WikaBabApprovalLine(models.Model):
    _name = 'wika.bap.approval.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    groups_id = fields.Many2one('res.groups', string='Groups', readonly=True)
    datetime = fields.Datetime('Date', readonly=True)
    note = fields.Char('Note', readonly=True)

class WikaPriceCutLine(models.Model):
    _name = 'wika.bap.pricecut.line'
    _description = 'Wika Price Cut Line'

    po_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    product_id = fields.Many2one('product.product', string='Product')
    amount = fields.Float(string='Amount')

