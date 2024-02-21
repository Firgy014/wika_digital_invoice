from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
from datetime import datetime,timedelta

class WikaInheritedAccountMove(models.Model):
    _inherit = 'account.move'
    
    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='BAP', required=True,domain=[('state','=','approved')])
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project', required=True, readonly=True)
    document_ids = fields.One2many('wika.invoice.document.line', 'invoice_id', string='Document Line', required=True)
    history_approval_ids = fields.One2many('wika.invoice.approval.line', 'invoice_id', string='History Approval Line')
    reject_reason_account = fields.Text(string='Reject Reason')
    step_approve = fields.Integer(string='Step Approve',default=1)
    no_doc_sap = fields.Char(string='No Doc SAP')
    no_invoice_vendor = fields.Char(string='Nomor Invoice Vendor',required=True)
    invoice_number = fields.Char(string='Invoice Number',required=True)
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
    total_pph = fields.Monetary(string='Total PPH', readonly=False, compute='')

    price_cut_ids = fields.One2many('wika.account.move.pricecut.line', 'move_id', string='Other Price Cut')
    account_id = fields.Many2one(comodel_name='account.account')
    date = fields.Date(string='Posting Date', default=lambda self: fields.Date.today())

    @api.onchange('pph_ids')
    def _onchange_pph_ids(self):
        pass
    
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

    @api.onchange('baseline_date')
    def _onchange_baseline_date(self):
        if isinstance(self, bool):
            return self
        if len(self) != 1:
            raise ValidationError("Hanya satu record yang diharapkan diperbarui!")
        
        if self.baseline_date != False and self.baseline_date < self.date:
            raise ValidationError("Baseline Date harus lebih atau sama dengan Posting Date!")
        else:
            pass

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

    # invoice_line_ids = fields.One2many(  # /!\ invoice_line_ids is just a subset of line_ids.
    #     'account.move.line',
    #     'move_id',
    #     string='Invoice lines',
    #     copy=False,
    #     readonly=True,
    #     domain=[('display_type', 'in', ('product', 'line_section', 'line_note'))],
    #     states={'draft': [('readonly', False)]},
    # )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('uploaded', 'Uploaded'),
            ('approved', 'Approved'),
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

    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)

    partner_id = fields.Many2one(
        'res.partner',
        string='Vendors',
        readonly=True,
        tracking=True,
        states={'draft': [('readonly', False)]},
        inverse='_inverse_partner_id',
        check_company=True,
        change_default=True,
        index=True,
        ondelete='restrict',
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
    no_faktur_pajak=fields.Char(string='Tax Number')

    @api.onchange('baseline_date')
    def _onchange_baseline_date(self):
        if self.baseline_date != False and self.baseline_date < self.date:
            raise ValidationError("Baseline Date harus lebih dan/atau sama dengan Posting Date!")
        else:
            pass


    def _compute_documents_count(self):
        for record in self:
            record.documents_count = self.env['documents.document'].search_count(
                [('purchase_id', '=', record.po_id.id)])

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

        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree',
            'res_model': 'documents.document',
            'view_ids': [(view_kanban_id, 'kanban'),(view_tree_id, 'tree')],
            'res_id': self.id,
            'domain': [('purchase_id', '=', self.po_id.id),('folder_id','in',('PO','GR/SES','BAP','Invoicing'))],
            'context': {'default_purchase_id': self.po_id.id},
        }

    @api.depends('project_id', 'branch_id', 'department_id')
    def _compute_level(self):
        for res in self:
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

    @api.depends('line_ids.price_unit', 'line_ids.quantity', 'line_ids.discount', 'line_ids.tax_ids')
    def _compute_amount_total(self):
        for move in self:
            amount_total_footer = 0.0
            for line in move.line_ids:
                price_subtotal = line.price_unit * line.quantity
                price_subtotal -= line.discount
                for tax in line.tax_ids:
                    price_subtotal += price_subtotal * tax.amount / 100

                amount_total_footer += price_subtotal

            move.amount_total_footer = amount_total_footer

    @api.onchange('partner_id','valuation_class')
    def onchange_account_payable(self):
        for record in self:
            record.account_id=False
            account_setting_model = self.env['wika.setting.account.payable'].sudo()

            if record.partner_id.bill_coa_type == 'relate':
                if record.level == 'Proyek' and record.valuation_class:
                    account_setting_id = account_setting_model.search([
                        ('valuation_class', '=', record.valuation_class),
                        ('assignment', '=', record.level.lower()),
                    ], limit=1)
                    record.account_id= account_setting_id.account_berelasi_id.id
                elif record.level != 'Proyek' and record.valuation_class:
                    account_setting_id = account_setting_model.search([
                        ('valuation_class', '=', record.valuation_class),
                        ('assignment', '=', 'nonproyek'),
                    ], limit=1)
                    record.account_id= account_setting_id.account_berelasi_id.id
            elif record.partner_id.bill_coa_type == '3rd_party':
                if record.level == 'Proyek' and record.valuation_class:
                    account_setting_id = account_setting_model.search([
                        ('valuation_class', '=', record.valuation_class),
                        ('assignment', '=', record.level.lower()),
                    ], limit=1)
                    record.account_id= account_setting_id.account_pihak_ketiga_id.id
                elif record.level != 'Proyek' and record.valuation_class:
                    account_setting_id = account_setting_model.search([
                        ('valuation_class', '=', record.valuation_class),
                        ('assignment', '=', 'nonproyek'),
                    ], limit=1)
                    record.account_id= account_setting_id.account_pihak_ketiga_id.id

    @api.model_create_multi
    def create(self, vals_list):
        record = super(WikaInheritedAccountMove, self).create(vals_list)
        record._check_invoice_totals()
        record.assign_todo_first()

        if isinstance(record, bool):
            return record
        if len(record) != 1:
            raise ValidationError("Hanya satu record yang diharapkan diperbarui!")

        # baseline date
        if record.baseline_date != False and record.baseline_date < record.date:
            raise ValidationError("Baseline Date harus lebih atau sama dengan Posting Date!")
        else:
            pass
        
        # document date
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
        self._check_invoice_totals()

        if isinstance(record, bool):
            return record
        if len(record) != 1:
            raise ValidationError("Hanya satu record yang diharapkan diperbarui!")

        # baseline date
        if record.baseline_date != False and record.baseline_date < record.date:
            raise ValidationError("Baseline Date harus lebih atau sama dengan Posting Date!")
        else:
            pass
        
        # document date
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


    # @api.onchange('amount_invoice')
    # def _onchange_amount_invoice(self):
    #     if self.amount_invoice and self.amount_invoice != self.amount_total_footer:
    #         warning = {
    #             'title': _('Warning!'),
    #             'message': _('Nilai dari "Amount Invoice" tidak sama dengan "Tax Totals".')
    #         }
    #         return {'warning': warning}

    def _check_invoice_totals(self):
        if self.amount_invoice and self.amount_invoice != self.amount_total_footer:
            raise ValidationError("Amount Invoice harus sama dengan Amount Total!")

    def _check_partner_payable_accounts(self):
        if self.partner_id.category_id != False:
            if self.partner_id.category_id.name == 'Berelasi':
                for lines in self.invoice_line_ids:
                    print(lines.name)
            # print(self.partner_id.category_id.name)

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
                    [('model_id', '=', model_id.id), ('level', '=', level)], limit=1)
                approval_line_id = self.env['wika.approval.setting.line'].search([
                    ('sequence', '=', 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                print(approval_line_id)
                groups_id = approval_line_id.groups_id
                if groups_id:
                    for x in groups_id.users:
                        if level == 'Proyek' and x.project_id == res.project_id:
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


    def action_submit(self):
        for record in self:
            if any(not line.document for line in record.document_ids):
                raise ValidationError('Document belum di unggah, mohon unggah file terlebih dahulu!')
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
            print(approval_line_id)
            groups_id = approval_line_id.groups_id
            if groups_id:
                for x in groups_id.users:
                    if level == 'Proyek' and x.project_id == self.project_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True

        if cek == True:
            first_user=False
            if self.activity_ids:
                for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                    print("masuk")
                    print(x.user_id)
                    if x.user_id.id == self._uid:
                        print(x.status)
                        x.status = 'approved'
                        x.action_done()
                self.state = 'uploaded'
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
                print("groups", groups_line)
                groups_id_next = groups_line.groups_id
                if groups_id_next:
                    print(groups_id_next.name)
                    for x in groups_id_next.users:
                        if level == 'Proyek' and x.project_id == self.project_id:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                            first_user = x.id
                    print(first_user)
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
        if level:
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
                print(groups_id.name)
                for x in groups_id.users:
                    if level == 'Proyek':
                        if x.project_id == self.project_id or x.branch_id == self.branch_id or x.branch_id.parent_id.code=='Pusat':
                            if x.id == self._uid:
                                cek = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True

        if cek == True:
            if approval_id.total_approve == self.step_approve:
                self.state = 'approved'
                self.env['wika.invoice.approval.line'].create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Approved',
                    'invoice_id': self.id
                })
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
                        print("masuk")
                        print(x.user_id)
                        if x.user_id.id == self._uid:
                            print(x.status)
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
                print("groups", groups_line_next)
                groups_id_next = groups_line_next.groups_id
                if groups_id_next:
                    print(groups_id_next.name)
                    for x in groups_id_next.users:
                        if level == 'Proyek' :
                            if x.project_id == self.project_id or x.branch_id == self.branch_id or x.branch_id.parent_id.code == 'Pusat':
                                first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                            first_user = x.id

                    print(first_user)
                    if first_user:
                        self.step_approve += 1
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
                        self.env['wika.invoice.approval.line'].create({
                            'user_id': self._uid,
                            'groups_id': groups_id.id,
                            'date': datetime.now(),
                            'note': 'Verified',
                            'invoice_id': self.id
                        })
                        if self.activity_ids:
                            for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                                print("masuk")
                                print(x.user_id)
                                if x.user_id.id == self._uid:
                                    print(x.status)
                                    x.status = 'approved'
                                    x.action_done()
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
                print(groups_id.name)
                for x in groups_id.users:
                    if x.project_id == self.project_id or x.branch_id == self.branch_id or x.branch_id.parent_id.code == 'Pusat':
                        if x.id == self._uid:
                            cek = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
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
    def _onchange_doc(self):
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
        return self.env.ref('wika_account_move.report_wika_account_move_action').report_action(self)   

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
