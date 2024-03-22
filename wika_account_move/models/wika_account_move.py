from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
from datetime import datetime,timedelta

class WikaInheritedAccountMove(models.Model):
    _inherit = 'account.move'
    
    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='BAP',domain=[('state','=','approved')])
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    document_ids = fields.One2many('wika.invoice.document.line', 'invoice_id', string='Document Line', required=True)
    history_approval_ids = fields.One2many('wika.invoice.approval.line', 'invoice_id', string='History Approval Line')
    reject_reason_account = fields.Text(string='Reject Reason')
    step_approve = fields.Integer(string='Step Approve',default=1)
    no_doc_sap = fields.Char(string='No Doc SAP')
    no_invoice_vendor = fields.Char(string='Nomor Invoice Vendor',required=True)
    invoice_number = fields.Char(string='Invoice Number')
    baseline_date = fields.Date(string='Baseline Date')
    retention_due = fields.Date(string='Retention Due')
    po_id = fields.Many2one('purchase.order', store=True, readonly=False,
        string='Nomor PO',domain=[('state','=','approved')])
    amount_invoice = fields.Float(string='Amount Invoice')
    tax_totals = fields.Binary(
        string="Invoice Totals",
        compute='_compute_tax_totals',
        inverse='_inverse_tax_totals',
        help='Edit Tax amounts if you encounter rounding issues.',
        exportable=False,
    )
    special_gl_id = fields.Many2one('wika.special.gl', string='Special GL')
    check_biro = fields.Boolean(compute="_cek_biro")

    pph_ids = fields.Many2many('account.tax', string='PPH')
    total_pph = fields.Monetary(string='Total PPH', readonly=False, compute='_compute_total_pph')
    pph_amount = fields.Monetary(string='PPH Amount', readonly=False)

    price_cut_ids = fields.One2many('wika.account.move.pricecut.line', 'move_id', string='Other Price Cut')
    account_id = fields.Many2one(comodel_name='account.account')
    date = fields.Date(string='Posting Date', default=lambda self: fields.Date.today())
    status_invoice = fields.Char(string='Status Invoice',compute='_compute_status_invoice')
    status_invoice_rel = fields.Char(string='Status Invoice',related='status_invoice',store=True)

    approval_stage = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat'),
    ], string='Position')
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
    is_approval_checked = fields.Boolean(string="Approval Checked", compute='_compute_is_approval_checked' ,default=False)
    is_wizard_cancel = fields.Boolean(string="Is cancel", default=True)
    is_mp_approved = fields.Boolean(string='Approved by MP', default=False, compute='_compute_mp_approved', store=True)

    @api.depends('history_approval_ids.user_id')
    def _compute_mp_approved(self):
        approval_setting_model = self.env['wika.approval.setting'].sudo()
        invoice_model_id = self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1)

        invoice_approval_setting_id = approval_setting_model.search([('model_id', '=', invoice_model_id.id)])
        if invoice_approval_setting_id:
            for set in invoice_approval_setting_id.setting_line_ids:
                if set.groups_id.name == 'MP':
                    if set.check_approval == True:
                        self.is_mp_approved = True

    @api.depends('history_approval_ids.is_show_wizard', 'history_approval_ids.user_id')
    def _compute_is_approval_checked(self):
        current_user = self.env.user
        for move in self:
            move.is_approval_checked = any(line.is_show_wizard for line in move.history_approval_ids if line.user_id == current_user)

    @api.depends('total_line', 'pph_ids.amount','pph_amount')
    def _compute_total_pph(self):
        for record in self:
            total_pph = 0.0
            if record.pph_amount>0:
                record.total_pph = record.pph_amount
            else:
                for pph in record.pph_ids:
                    total_pph += (record.total_line* pph.amount) / 100
                record.total_pph = total_pph


    @api.depends('history_approval_ids')
    def _compute_status_invoice(self):
        for record in self:
            max_id = max(record.history_approval_ids.mapped('id'), default=False)
            current_user = record.user_id
            if max_id:
                max_record = record.history_approval_ids.filtered(lambda x: x.id == max_id)
                record.status_invoice = f"{max_record.note} by {max_record.groups_id.name}"
            else:
                record.status_invoice = f"Created by {current_user.name}"

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



    @api.onchange('invoice_date')
    def _onchange_invoice_date(self):
        if isinstance(self, bool):
            return self
        if len(self) != 1:
            raise ValidationError("Hanya satu record yang diharapkan diperbarui!")

        if self.invoice_date != False and self.invoice_date < self.bap_id.bap_date:
            raise ValidationError("Document Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")
        else:
            pass

    @api.onchange('date')
    def _onchange_posting_date(self):
        if not self.date or not self.bap_id or not self.bap_id.bap_date:
            return
        if isinstance(self, bool):
            return self
        if len(self) != 1:
            raise ValidationError("Hanya satu record yang diharapkan diperbarui!")
        if self.date < self.bap_id.bap_date:
            raise ValidationError("Posting Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('uploaded', 'Uploaded'),
            ('approved', 'Approved'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )
    amount_total_footer = fields.Float(string='Amount Total', compute='_compute_amount_total', store=True)
    level = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat')
    ], string='Level', compute='_compute_level', default='Proyek')
    valuation_class = fields.Selection([
        ('material', 'Material'),
        ('alat', 'Alat'),
        ('upah', 'Upah'),
        ('subkont', 'Subkont'),
        ('btl', 'BTL')
    ], compute='_compute_get_lowest_valuation_class', string='Valuation Class')

    documents_count = fields.Integer(string='Total Doc', compute='_compute_documents_count')
    no_faktur_pajak = fields.Char(string='Tax Number')
    dp_total = fields.Float(string='Total DP', compute='_compute_potongan_total', store= True)
    retensi_total = fields.Float(string='Total Retensi', compute='_compute_potongan_total', store= True)
    total_tax = fields.Monetary(string='Total Tax', compute='compute_total_tax')

    amount_total_payment = fields.Float(string='Total Invoice', compute='_compute_amount_total_payment', store=True)
    total_line = fields.Float(string='Total Line', compute='_compute_total_line')
    cut_off = fields.Boolean(string='Cut Off',default=False,copy=False)
    # is_approval_checked = fields.Boolean(string="Approval Checked")

    @api.depends('total_line', 'invoice_line_ids', 'dp_total','retensi_total', 'invoice_line_ids.tax_ids')
    def compute_total_tax(self):
        for record in self:
            total_line = record.total_line or 0.0
            dp_total = record.dp_total or 0.0
            retensi_total = record.retensi_total or 0.0
            tax_percentage = sum(record.invoice_line_ids.tax_ids.mapped('amount')) / 100.0
            total_tax = (total_line - dp_total - retensi_total) * tax_percentage
            record.total_tax = total_tax

    @api.depends('total_line', 'price_cut_ids.percentage_amount','price_cut_ids.product_id')
    def _compute_potongan_total(self):
        for x in self:
            persentage_dp=sum(line.percentage_amount for line in x.price_cut_ids  if line.product_id.name == 'DP')
            persentage_retensi=sum(line.percentage_amount for line in x.price_cut_ids  if line.product_id.name == 'RETENSI')
            x.dp_total = 0.0
            x.retensi_total=0.0
            if persentage_dp > 0:
                x.dp_total = (x.total_line / 100 ) * persentage_dp
            if persentage_retensi >0:
                x.retensi_total = (x.total_line / 100 ) * persentage_retensi

    @api.depends('total_line', 'dp_total', 'retensi_total','total_pph','total_tax')
    def _compute_amount_total_payment(self):
        for x in self:
            x.amount_total_payment= x.total_line-x.dp_total-x.retensi_total + x.total_tax -x.total_pph


    def _compute_documents_count(self):
        for record in self:
            domain = [
                ('folder_id', 'in', ['PO', 'GR/SES', 'BAP', 'Invoicing']),
                '|', ('bap_id', '=', self.bap_id.id), ('bap_id', '=', False), ('purchase_id', '=', self.po_id.id)
            ]
            
            po_number = self.po_id.name if self.po_id else None

            if po_number:
                domain.append(('purchase_id.name', '=', po_number))
            
            # if record.bap_id:
            #     domain.append(('bap_id', '=', record.bap_id.id))

            record.documents_count = self.env['documents.document'].search_count(domain)


    @api.depends('invoice_line_ids')
    def _compute_get_lowest_valuation_class(self):
        valuation_classes = [line.product_id.valuation_class for line in self.invoice_line_ids if
                             line.product_id and line.product_id.valuation_class]
        if valuation_classes:
            self.valuation_class = min(valuation_classes)
        else:
            self.valuation_class = False

    def get_documents(self):
        self.ensure_one()
        view_kanban_id = self.env.ref("documents.document_view_kanban", raise_if_not_found=False)
        view_tree_id = self.env.ref("documents.documents_view_list", raise_if_not_found=False)

        domain = [
            ('folder_id', 'in', ['PO', 'GR/SES', 'BAP', 'Invoicing']),
            '|', ('bap_id', '=', self.bap_id.id), ('bap_id', '=', False), ('purchase_id', '=', self.po_id.id)
        ]

        po_number = self.po_id.name if self.po_id else None

        if po_number:
            domain.append(('purchase_id.name', '=', po_number))
            
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree',
            'res_model': 'documents.document',
            'view_ids': [(view_kanban_id.id, 'kanban'), (view_tree_id.id, 'tree')],
            'res_id': self.id,
            'domain': domain,
            'context': {'default_purchase_id': self.po_id.id},
        }

    @api.depends('project_id', 'branch_id', 'department_id')
    def _compute_level(self):
        for res in self:
            level=False
            if res.project_id:
                level = 'Proyek'
            elif res.branch_id and not res.department_id and not res.project_id:
                level = 'Divisi Operasi'
            elif res.branch_id and res.department_id and not res.project_id:
                level = 'Divisi Fungsi'
            res.level = level

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            domain = [('partner_id', '=', self.partner_id.id)]
            return {'domain': {'bap_id': domain}}
        else:
            return {'domain': {'bap_id': []}}

    @api.depends('invoice_line_ids.price_unit','invoice_line_ids.quantity')
    def _compute_total_line(self):
        for x in self:
            total = 0
            for z in x.invoice_line_ids:
                total += z.price_unit *z.quantity
            x.total_line = total

    @api.depends('total_line', 'total_pph','dp_total','retensi_total')
    def _compute_amount_total(self):
        for move in self:
            move.amount_total_footer = move.total_line-move.dp_total-move.retensi_total -move.total_pph

    @api.onchange('partner_id', 'valuation_class')
    def onchange_account_payable(self):
        for record in self:
            record.account_id = False
            account_setting_model = self.env['wika.setting.account.payable'].sudo()
            if record.level == 'Proyek' and record.valuation_class:
                account_setting_id = account_setting_model.search([
                    ('valuation_class', '=', record.valuation_class),
                    ('assignment', '=', record.level.lower()),
                    ('bill_coa_type', '=', record.partner_id.bill_coa_type)
                ], limit=1)
                record.account_id = account_setting_id.account_id.id
            elif record.level != 'Proyek' and record.valuation_class:
                account_setting_id = account_setting_model.search([
                    ('valuation_class', '=', record.valuation_class),
                    ('assignment', '=', 'nonproyek'),
                    ('bill_coa_type', '=',  record.partner_id.bill_coa_type)
                ], limit=1)
                record.account_id = account_setting_id.account_id.id


    @api.model_create_multi
    def create(self, vals_list):
        record = super(WikaInheritedAccountMove, self).create(vals_list)
        record._check_invoice_totals()
        record.assign_todo_first()

        if isinstance(record, bool):
            return record
        if len(record) != 1:
            raise ValidationError("Hanya satu record yang diharapkan diperbarui!")

        
        #document date
        if record.invoice_date != False and record.invoice_date < record.bap_id.bap_date:
            raise ValidationError("Document Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")
        else:
            pass

       # posting date
        if record.date != False and record.date < record.bap_id.bap_date:
            raise ValidationError("Posting Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")
        else:
            pass

        return record

    def write(self, values):
        record = super(WikaInheritedAccountMove, self).write(values)
        if isinstance(record, bool):
            return record
        if len(record) != 1:
            raise ValidationError("Hanya satu record yang diharapkan diperbarui!")


        
        #document date
        if record.invoice_date != False and record.invoice_date < record.bap_id.bap_date:
            raise ValidationError("Document Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")
        else:
            pass

        # posting date
        if record.date != False and record.date < record.bap_id.bap_date:
            raise ValidationError("Posting Date harus lebih atau sama dengan Tanggal BAP yang dipilih!")
        else:
            pass
        return record


    @api.onchange('amount_invoice')
    def _onchange_amount_invoice(self):
        if self.amount_invoice and self.amount_invoice != self.amount_total_footer:
            warning = {
                'title': _('Warning!'),
                'message': _('Nilai dari "Amount Invoice" tidak sama dengan "Tax Totals".')
            }
            return {'warning': warning}

    def _check_invoice_totals(self):
        if self.amount_invoice < round(self.total_line) or self.amount_invoice > round(self.total_line):
            raise ValidationError('Amount Invoice Harus sama dengan Total !')


    @api.onchange('bap_id')
    def _onchange_bap_id(self):
        self.po_id = False
        if self.bap_id:
            invoice_lines = []
            price_cut_lines = []

            self.po_id = self.bap_id.po_id.id
            self.partner_id = self.bap_id.po_id.partner_id.id
            self.branch_id = self.bap_id.branch_id.id
            self.department_id = self.bap_id.department_id.id if self.bap_id.department_id else False
            self.project_id = self.bap_id.project_id.id if self.bap_id.project_id else False

            self.pph_ids = self.bap_id.pph_ids.ids
            self.total_pph = self.bap_id.total_pph

            for bap_line in self.bap_id.bap_ids:
                print (bap_line.qty)
                invoice_lines.append((0, 0, {
                    'display_type':'product',
                    'product_id': bap_line.product_id.id,
                    'purchase_line_id': bap_line.purchase_line_id.id,
                    'bap_line_id': bap_line.id,
                    'picking_id': bap_line.picking_id.id,
                    'stock_move_id': bap_line.stock_move_id.id,
                    'quantity': bap_line.qty,
                    'price_unit': bap_line.unit_price,
                    'tax_ids': bap_line.purchase_line_id.taxes_id.ids,
                    'product_uom_id': bap_line.product_uom.id,
                }))

            for cut_line in self.bap_id.price_cut_ids:
                price_cut_lines.append((0, 0, {
                    'move_id': self.id,
                    'product_id': cut_line.product_id.id,
                    # 'account_id': cut_line.account_id.id,
                    'percentage_amount': cut_line.percentage_amount,
                    'amount': cut_line.amount,
                }))

            self.invoice_line_ids = invoice_lines
            self.price_cut_ids = price_cut_lines

    def assign_todo_first(self):
        model_model = self.env['ir.model'].sudo()
        model_id = model_model.search([('model', '=', 'account.move')], limit=1)
        for res in self:

            level=res.level
            first_user = False
            if level:
                approval_id = self.env['wika.approval.setting'].sudo().search(
                    [ ('model_id', '=', model_id.id),('transaction_type', '!=', 'pr'),('level', '=', level)], limit=1)
                approval_line_id = self.env['wika.approval.setting.line'].search([
                    ('sequence', '=', 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                groups_id = approval_line_id.groups_id
                if groups_id:
                    for x in groups_id.users:
                        if level == 'Proyek' and  res.project_id in x.project_ids:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == res.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == res.department_id:
                            first_user = x.id
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
                    res.approval_stage=level
            model_model = self.env['ir.model'].sudo()
            document_setting_model = self.env['wika.document.setting'].sudo()
            model_id = model_model.search([('model', '=', 'account.move')], limit=1)
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

            document_list = []
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])
            if doc_setting_id:
                for document_line in doc_setting_id:
                    document_list.append((0, 0, {
                        'invoice_id': self.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                self.document_ids = document_list
            else:
                raise AccessError("Data dokumen tidak ada!")

    def action_submit(self):
        for record in self:
            if any(not line.document for line in record.document_ids):
                raise ValidationError('Document belum di unggah, mohon unggah file terlebih dahulu!')
        for record in self:
            if any(line.state =='rejected' for line in record.document_ids):
                raise ValidationError('Document belum di ubah setelah reject, silahkan cek terlebih dahulu!')
        cek = False
        level=self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu Invoice tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', 1),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            groups_id = approval_line_id.groups_id
            if groups_id:
                if self.activity_user_id.id == self._uid:
                    cek = True

        if cek == True:
            first_user = False
            if self.activity_ids:
                for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                    if x.user_id.id == self._uid:
                        x.status = 'approved'
                        x.action_done()
                self.state = 'uploaded'
                self.approval_stage = approval_line_id.level_role
                self.step_approve += 1
                self.env['wika.invoice.approval.line'].sudo().create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Submit Document',
                    'invoice_id': self.id
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
                                [('model', '=', 'account.move')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'nomor_po': self.po_id.name,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': """Need Approval Document Invoice"""
                        })
        else:
            raise ValidationError('User Akses Anda tidak berhak Submit!')

    def action_approve(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        documents_model = self.env['documents.document'].sudo()
        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
        level = self.level
        is_mp = False
        if level:
            keterangan = ''
            if level == 'Proyek':
                keterangan = '''<p><strong>Dengan ini Kami Menyatakan:</strong></p>
                                <ol>
                                    <li>Bahwa Menjamin dan Bertanggung Jawab Atas Kebenaran, Keabsahan
                                    Bukti Transaksi Beserta Bukti Pendukungnya, Dan Dokumen Yang Telah Di
                                    Upload Sesuai Dengan Aslinya.</li>
                                    <li>Bahwa Mitra Kerja Tersebut telah melaksanakan pekerjaan Sebagaimana
                                    Yang Telah Dipersyaratkan di Dalam Kontrak, Sehingga Memenuhi Syarat
                                    Untuk Dibayar.</li>
                                </ol>
                                <p>Copy Dokumen Bukti Transaksi :</p>
                                <ul>
                                    <li>PO SAP</li>
                                    <li>Dokumen Kontrak Lengkap</li>
                                    <li>GR/SES</li>
                                    <li>Surat Jalan (untuk material)</li>
                                    <li>BAP</li>
                                    <li>Invoice</li>
                                    <li>Faktur Pajak</li>
                                </ul>'''
            elif level == 'Divisi Operasi':
                keterangan = '''<p>Kami Telah Melakukan Verifikasi Kelengkapan, Keabsahan Bukti Transaksi Dan Setuju Untuk Dibayarkan</p>
                                <p>Copy Dokumen Bukti Transaksi :</p>
                                <ul>
                                    <li>PO SAP</li>
                                    <li>Dokumen Kontrak Lengkap</li>
                                    <li>GR/SES</li>
                                    <li>Surat Jalan (untuk material)</li>
                                    <li>BAP</li>
                                    <li>Invoice</li>
                                    <li>Faktur Pajak</li>
                                </ul>'''
            elif level == 'Divisi Fungsi':
                keterangan = '''<p>Kami Telah Melakukan Verifikasi Kelengkapan Dokumen Dan Menyetujui Pembayaran Transaksi ini.</p>
                                <p>Copy Dokumen Bukti Transaksi :</p>
                                <ul>
                                    <li>PO SAP</li>
                                    <li>Dokumen Kontrak Lengkap</li>
                                    <li>GR/SES</li>
                                    <li>Surat Jalan (untuk material)</li>
                                    <li>BAP</li>
                                    <li>Invoice</li>
                                    <li>Faktur Pajak</li>
                                </ul>'''
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu Invoice tidak ditemukan. Silakan hubungi Administrator!')

            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            groups_id = approval_line_id.groups_id
            if groups_id:
                for x in groups_id.users:
                    if level == 'Proyek':
                        if self.project_id in x.project_ids or x.branch_id == self.branch_id or x.branch_id.parent_id.code=='Pusat':
                            if x.id == self._uid:
                                cek = True
                                is_mp = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True

        if cek == True:
            if approval_id.total_approve == self.step_approve:
                self.state = 'approved'
                self.approval_stage = 'Pusat'
                if is_mp:
                    self.baseline_date = fields.Date.today()

                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'Invoicing')], limit=1)
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
                                'partner_id': self.partner_id.id,
                                'purchase_id': self.bap_id.po_id.id,
                                'invoice_id': self.id,

                            })
                if self.activity_ids:
                    for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                        if x.user_id.id == self._uid:
                            print(x.status)
                            x.status = 'approved'
                            x.action_done()
                self.env['wika.invoice.approval.line'].create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Approved',
                    'invoice_id': self.id,
                    'information': keterangan if approval_line_id.check_approval else False,
                    'is_show_wizard': True if approval_line_id.check_approval else False,

                })
                if approval_line_id.check_approval:
                    action = {
                        'type': 'ir.actions.act_window',
                        'name': 'Approval Wizard',
                        'res_model': 'approval.wizard.account.move',
                        'view_type': "form",
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_keterangan': keterangan
                        },
                        'view_id': self.env.ref('wika_account_move.approval_wizard_form').id,
                    }
                    return action

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
                    if first_user:
                        self.step_approve += 1
                        self.approval_stage = groups_line_next.level_role
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'res_model_id': self.env['ir.model'].sudo().search(
                                [('model', '=', 'account.move')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'nomor_po': self.po_id.name,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': """Need Approval Document Invoicing"""
                        })

                        if self.activity_ids:
                            for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                                if x.user_id.id == self._uid:
                                    x.status = 'approved'
                                    x.action_done()
                        self.env['wika.invoice.approval.line'].create({
                            'user_id': self._uid,
                            'groups_id': groups_id.id,
                            'date': datetime.now(),
                            'note': 'Verified',
                            'invoice_id': self.id,
                            'information': keterangan if approval_line_id.check_approval else False,
                            'is_show_wizard': True if approval_line_id.check_approval else False,

                        })
                        if approval_line_id.check_approval:
                            print("Approval Line ID:", approval_line_id.check_approval)
                            action = {
                                'type': 'ir.actions.act_window',
                                'name': 'Approval Wizard',
                                'res_model': 'approval.wizard.account.move',
                                'view_type': "form",
                                'view_mode': 'form',
                                'target': 'new',
                                'context': {
                                    'default_keterangan': keterangan
                                },
                                'view_id': self.env.ref('wika_account_move.approval_wizard_form').id,
                            }
                            return action

                    else:
                        raise ValidationError('User Role Next Approval Belum di Setting!')

        else:
            raise ValidationError('User Akses Anda tidak berhak Approve!')

    def action_reject(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        cek = False
        level = self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu Invoice tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            print(approval_line_id)
            groups_id = approval_line_id.groups_id
            if groups_id:
                if self.activity_user_id.id == self._uid:
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




    def unlink(self):
        for record in self:
            if record.state in ('upload', 'approve'):
                raise ValidationError('Tidak dapat menghapus ketika status Vendor Bils dalam keadaan Upload atau Approve')
        return super(WikaInheritedAccountMove, self).unlink()

    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        self = self.sorted(lambda m: (m.date, m.ref or '', m.id))

        for move in self:
            move_has_name = move.name and move.name != '/'
            if move_has_name or move.state != 'draft':
                if not move.posted_before and not move._sequence_matches_date():
                    if move._get_last_sequence(lock=False):
                        # The name does not match the date and the move is not the first in the period:
                        # Reset to draft
                        move.name = False
                        continue
                else:
                    if move_has_name and move.posted_before or not move_has_name and move._get_last_sequence(lock=False):
                        # The move either
                        # - has a name and was posted before, or
                        # - doesn't have a name, but is not the first in the period
                        # so we don't recompute the name
                        continue
            if move.date and (not move_has_name or not move._sequence_matches_date()):
                move._set_next_sequence()

        self.filtered(lambda m: not m.name and not move.quick_edit_mode).name = '/'
        self._inverse_name()

    def action_print_invoice(self):
        if self.level == 'Proyek':
            return self.env.ref('wika_account_move.report_wika_account_move_proyek_action').report_action(self)
        elif self.level == 'Divisi Operasi':
            return self.env.ref('wika_account_move.report_wika_account_move_divisi_action').report_action(self)
        elif self.level == 'Divisi Fungsi':
            return self.env.ref('wika_account_move.report_wika_account_move_keuangan_action').report_action(self)
        elif self.level == 'Pusat':
            return self.env.ref('wika_account_move.report_wika_account_move_keuangan_action').report_action(self)
        else:
            return super(WikaInheritedAccountMove, self).action_print_invoice()


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
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
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
            
class WikaInvoiceApprovalLine(models.Model):
    _name = 'wika.invoice.approval.line'
    _description = 'Wika Approval Line'

    invoice_id = fields.Many2one('account.move', string='Invoice id')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
    information = fields.Char(string='Keterangan')
    is_show_wizard = fields.Boolean('check')

class AccountMovePriceCutList(models.Model):
    _name = 'wika.account.move.pricecut.line'

    move_id = fields.Many2one('account.move', string='Invoice')
    move_line_id = fields.Many2one('account.move.line', string='Invoice Line')
    special_gl_id = fields.Many2one('wika.special.gl', string='Special GL')
    product_id = fields.Many2one('product.product', string='Product')
    account_id = fields.Many2one('account.account', string='Account', compute='_compute_account_pricecut')
    percentage_amount = fields.Float(string='Percentage Amount')
    amount = fields.Float(string='Amount')
    
    def _compute_account_pricecut(self):
        move_id = self.env['account.move'].browse([self.move_id.id])
        if move_id:            
            self.account_id = move_id.line_ids[0].account_id.id

class WikaAccountTax(models.Model):
    _inherit = 'account.tax'

    pph_code = fields.Char(string='PPH Code', compute='_compute_pph_code', store=True)

    @api.depends('name')
    def _compute_pph_code(self):
        for record in self:
            if record.name:
                record.pph_code = record.name[0:2]

class WikaAccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    pph_group_code = fields.Char(string='PPH Group Code', compute='_compute_pph_group_code', store=True)

    @api.depends('name')
    def _compute_pph_group_code(self):
        for record in self:
            if record.name:
                record.pph_group_code = record.name[0:2]