from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
from datetime import datetime

class WikaInheritedAccountMove(models.Model):
    _inherit = 'account.move'
    
    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='BAP', required=True)
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department', required=True)
    project_id = fields.Many2one('project.project', string='Project', required=True, readonly=True)
    document_ids = fields.One2many('wika.invoice.document.line', 'invoice_id', string='Document Line', required=True)
    history_approval_ids = fields.One2many('wika.invoice.approval.line', 'invoice_id', string='History Approval Line')
    reject_reason_account = fields.Text(string='Reject Reason')
    step_approve = fields.Integer(string='Step Approve')
    no_doc_sap = fields.Char(string='No Doc SAP')
    no_invoice_vendor = fields.Char(string='Nomor Invoice Vendor')
    invoice_number = fields.Char(string='Invoice Number', size=16)
    baseline_date = fields.Date(string='Baseline Date')
    retention_due = fields.Date(string='Retentstring=ion Due')
    amount_invoice = fields.Float(string='Amount Invoice')
    tax_totals = fields.Binary(
        string="Invoice Totals",
        compute='_compute_tax_totals',
        inverse='_inverse_tax_totals',
        help='Edit Tax amounts if you encounter rounding issues.',
        exportable=False,
    )
    special_gl_id = fields.Many2one('wika.special.gl', string='Special GL')
    invoice_line_ids = fields.One2many(  # /!\ invoice_line_ids is just a subset of line_ids.
        'account.move.line',
        'move_id',
        string='Invoice lines',
        copy=False,
        readonly=True,
        domain=[('display_type', 'in', ('product', 'line_section', 'line_note'))],
        states={'draft': [('readonly', False)]},
    )
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

    # @api.depends('invoice_line_ids')
    # def _compute_get_lowest_valuation_class(self):
    #     field_valuation_class = min(line.product_id.valuation_class for line in self.invoice_line_ids if line.product_id and line.product_id.valuation_class)
    #     if field_valuation_class:
    #         self.valuation_class = field_valuation_class
    #     else:
    #         self.valuation_class = False

    @api.depends('invoice_line_ids')
    def _compute_get_lowest_valuation_class(self):
        valuation_classes = [line.product_id.valuation_class for line in self.invoice_line_ids if line.product_id and line.product_id.valuation_class]
        if valuation_classes:
            self.valuation_class = min(valuation_classes)
        else:
            self.valuation_class = False


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

    @api.model_create_multi
    def create(self, values):
        account_setting_model = self.env['wika.setting.account.payable'].sudo()
        record = super(WikaInheritedAccountMove, self).create(values)
        record._check_invoice_totals()

        # Delete the duplicated COGS first
        i = 0
        lines_new_payable = []
        while i < len(record.line_ids) - 1:
            if record.line_ids[i].account_id.name == record.line_ids[i+1].account_id.name:
                record.line_ids[i].unlink()
            i += 1

        # Assign the COA
        # for line in record.line_ids:
        if record.partner_id.bill_coa_type == 'relate':
            if record.level == 'Proyek' and record.valuation_class != False:
                account_setting_id = account_setting_model.search([
                    # ('valuation_class', '=', line.product_id.valuation_class),
                    ('valuation_class', '=', record.valuation_class),
                    ('assignment', '=', record.level.lower()),
                ], limit=1)
                if account_setting_id != False:
                    lines_new_payable.append((0, 0, {
                        'account_id': account_setting_id.account_berelasi_id.id,
                        'display_type': 'payment_term',
                        'name': "Berelasi",
                        'debit': 0.0,
                        'credit': record.amount_total_footer
                    }))
                else:
                    raise ValidationError("COA untuk Invoice ini tidak ditemukan, silakan hubungi Administrator!")
                                    
        elif record.partner_id.bill_coa_type == '3rd_party':
            if record.level == 'Proyek' and record.valuation_class != False:
                account_setting_id = account_setting_model.search([
                    # ('valuation_class', '=', line.product_id.valuation_class),
                    ('valuation_class', '=', record.valuation_class),
                    ('assignment', '=', record.level.lower()),
                ])
                if account_setting_id != False:
                    lines_new_payable.append((0, 0, {
                        'account_id': account_setting_id.account_pihak_ketiga_id.id,
                        'display_type': 'payment_term',
                        'name': "Pihak Ketiga",
                        'debit': 0.0,
                        'credit': record.amount_total_footer
                    }))
                else:
                    raise ValidationError("COA untuk Invoice ini tidak ditemukan, silakan hubungi Administrator!")
        
        # Replace the payable COA
        for line_coa in record.line_ids:
            if line_coa.account_id.name == 'Trade Receivable':
                for new_coa in lines_new_payable:
                    line_coa.write(new_coa[2])

        return record

    def write(self, values):
        account_setting_model = self.env['wika.setting.account.payable'].sudo()
        record = super(WikaInheritedAccountMove, self).write(values)
        self._check_invoice_totals()

        # Assign the COA
        lines_new_payable = []
        if record.partner_id.bill_coa_type == 'relate':
            if record.level == 'Proyek' and record.valuation_class != False:
                account_setting_id = account_setting_model.search([
                    # ('valuation_class', '=', line.product_id.valuation_class),
                    ('valuation_class', '=', record.valuation_class),
                    ('assignment', '=', record.level.lower()),
                ], limit=1)
                if account_setting_id != False:
                    lines_new_payable.append((0, 0, {
                        'account_id': account_setting_id.account_berelasi_id.id,
                        'display_type': 'payment_term',
                        'name': "Berelasi",
                        'debit': 0.0,
                        'credit': record.amount_total_footer
                    }))
                else:
                    raise ValidationError("COA untuk Invoice ini tidak ditemukan, silakan hubungi Administrator!")
                                    
        elif record.partner_id.bill_coa_type == '3rd_party':
            if record.level == 'Proyek' and record.valuation_class != False:
                account_setting_id = account_setting_model.search([
                    # ('valuation_class', '=', line.product_id.valuation_class),
                    ('valuation_class', '=', record.valuation_class),
                    ('assignment', '=', record.level.lower()),
                ])
                if account_setting_id != False:
                    lines_new_payable.append((0, 0, {
                        'account_id': account_setting_id.account_pihak_ketiga_id.id,
                        'display_type': 'payment_term',
                        'name': "Pihak Ketiga",
                        'debit': 0.0,
                        'credit': record.amount_total_footer
                    }))
                else:
                    raise ValidationError("COA untuk Invoice ini tidak ditemukan, silakan hubungi Administrator!")
        
        # Replace the payable COA
        for line_coa in record.line_ids:
            if line_coa.account_id.name == 'Trade Receivable':
                for new_coa in lines_new_payable:
                    line_coa.write(new_coa[2])

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
        if self.bap_id:
            lines = []
            for bap_line in self.bap_id.bap_ids:
                lines.append((0, 0, {
                    'product_id': bap_line.product_id.id,
                    'quantity': bap_line.qty,
                    'price_unit': bap_line.unit_price,
                }))

            self.invoice_line_ids = lines

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
                        'summary': """ Need Approval Document Invoice """
                    })

        for record in self:
            if any(not line.document for line in record.document_ids):
                raise ValidationError('Document belum di unggah, mohon unggah file terlebih dahulu!')

    def action_approve(self):
        user = self.env['res.users'].search([('id','=',self._uid)], limit=1)
        documents_model = self.env['documents.document'].sudo()
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
                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'Invoice')], limit=1)
                if folder_id:
                    facet_id = self.env['documents.facet'].sudo().search([
                        ('name', '=', 'Vendor Bills'),
                        ('folder_id', '=', folder_id.id)
                    ], limit=1)
                    for doc in self.document_ids.filtered(lambda x: x.state == 'uploaded'):
                        doc.state = 'verif'
                        attachment_id = self.env['ir.attachment'].sudo().create({
                            'name': doc.filename,
                            'datas': doc.document,
                            'res_model': 'documents.document',
                        })
                        if attachment_id:
                            documents_model.create({
                                'attachment_id': attachment_id.id,
                                'folder_id': folder_id.id,
                                'tag_ids': facet_id.tag_ids.ids,
                                'partner_id': doc.invoice_id.partner_id.id,
                            })
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
            
class WikaInvoiceApprovalLine(models.Model):
    _name = 'wika.invoice.approval.line'
    _description = 'Wika Approval Line'

    invoice_id = fields.Many2one('account.move', string='Invoice id')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
