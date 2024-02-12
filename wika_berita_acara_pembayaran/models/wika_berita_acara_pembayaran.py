from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, Warning, AccessError

class WikaBeritaAcaraPembayaran(models.Model):
    _name = 'wika.berita.acara.pembayaran'
    _description = 'Berita Acara Pembayaran'
    _inherit = ['mail.thread']

    name = fields.Char(string='Nomor BAP', readonly=True, default='/')
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True, related="po_id.branch_id")
    department_id = fields.Many2one('res.branch', string='Department', related="po_id.department_id")
    project_id = fields.Many2one('project.project', string='Project', related="po_id.project_id")
    # po_id = fields.Many2one('purchase.order', string='Nomor PO', required=True,domain=[('state','=','approved')])
    po_id = fields.Many2one('purchase.order', string='Nomor PO')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    bap_ids = fields.One2many('wika.berita.acara.pembayaran.line', 'bap_id', string='List BAP', required=True)
    document_ids = fields.One2many('wika.bap.document.line', 'bap_id', string='List Document')
    history_approval_ids = fields.One2many('wika.bap.approval.line', 'bap_id', string='List Approval')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    state = fields.Selection([
        ('draft', 'Draft'), 
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')], string='Status', readonly=True, default='draft')
    reject_reason = fields.Text(string='Reject Reason')
    step_approve = fields.Integer(string='step approve',default=1)
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user",)
    end_date = fields.Date(string='Tgl Akhir Kontrak', related="po_id.end_date")
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
    currency_id = fields.Many2one('res.currency', string='Currency')
    notes = fields.Html(string='Terms and Conditions', store=True, readonly=False,)
    total_amount = fields.Monetary(string='Total Amount', compute='compute_total_amount')
    total_tax = fields.Monetary(string='Total Tax', compute='compute_total_tax')
    grand_total = fields.Monetary(string='Grand Total', compute='compute_grand_total')
    check_biro = fields.Boolean(compute="_cek_biro")
    tax_totals = fields.Float(
        string="Invoice Totals",
        compute='_compute_tax_totals',
        inverse='_inverse_tax_totals',
        help='Edit Tax amounts if you encounter rounding issues.',
        exportable=False,
    )
    # total_current_value = fields.Float(string='Total Current Value', compute='_compute_total_current_value') #buat sum nilai saat ini
    total_qty_gr = fields.Integer(string='Total Quantity', compute='_compute_total_qty_gr')
    total_unit_price_po = fields.Float(string='Total Unit Price PO', compute='_compute_total_unit_price_po')
    total_current_value = fields.Float(string='Total GR PO', compute='_compute_total_current_value') #buat sum nilai saat ini
    level = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat')
    ], string='Level',compute='_compute_level')


    @api.depends('project_id','branch_id','department_id')
    def _compute_level(self):

        for res in self:
            level=''
            if res.project_id:
                level = 'Proyek'
            elif res.branch_id and not res.department_id and not res.project_id:
                level = 'Divisi Operasi'
            elif res.branch_id and res.department_id and not res.project_id:
                level = 'Divisi Fungsi'
            res.level=level

    #compute total qty gr
    @api.depends('bap_ids.qty')
    def _compute_total_qty_gr(self):
        for record in self:
            total_qty = sum(line.qty for line in record.bap_ids)
            record.total_qty_gr = total_qty

    #compute total unit price PO
    @api.depends('bap_ids.unit_price_po')
    def _compute_total_unit_price_po(self):
        for record in self:
            total_unit_price = sum(line.unit_price_po for line in record.bap_ids)
            record.total_unit_price_po = total_unit_price

    #compute unit price po * qty gr
    @api.depends('bap_ids.qty', 'bap_ids.unit_price_po')
    def _compute_total_current_value(self):
        for record in self:
            total_qty = sum(line.qty for line in record.bap_ids)
            total_unit_price_po = sum(line.unit_price_po for line in record.bap_ids)
            record.total_current_value = total_qty * total_unit_price_po

    @api.model
    def create(self, vals):
        res = super(WikaBeritaAcaraPembayaran, self).create(vals)
        res.name= self.env['ir.sequence'].next_by_code('wika.berita.acara.pembayaran')
        res.assign_todo_first()
        return res



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
                
    @api.onchange('po_id')
    def onchange_po_id(self):
        if self.po_id:
            self.bap_ids = [(5, 0, 0)]
            
            stock_pickings = self.env['stock.picking'].search([('po_id', '=', self.po_id.id)])
            
            bap_lines = []
            for picking in stock_pickings.move_ids_without_package:
                pol_src = self.env['purchase.order.line'].search([
                    ('order_id', '=', picking.picking_id.po_id.id), 
                    ('product_id', '=', picking.product_id.id)])

                # aml_src = self.env['account.move.line'].search([
                #     ('move_id', '=', picking.picking_id.po_id.id), 
                #     ('product_id', '=', picking.product_id.id)])

                bap_lines.append((0, 0, {
                    'picking_id': picking.picking_id.id,
                    'purchase_line_id':pol_src.id or False,
                    'unit_price_po':pol_src.price_unit,
                    # 'account_move_line_id':aml_src.id or False,
                    'product_uom':picking.product_uom,
                    'product_id': picking.product_id.id,
                    'qty': picking.product_uom_qty,
                    'unit_price': picking.purchase_line_id.price_unit,
                    'tax_ids':picking.purchase_line_id.taxes_id.ids,
                    'currency_id':picking.purchase_line_id.currency_id.id
                }))      
            self.bap_ids = bap_lines

    @api.depends('bap_ids.sub_total', 'bap_ids.tax_ids')
    def compute_total_amount(self):
        for record in self:
            total_amount_value = sum(record.bap_ids.mapped('sub_total'))
            record.total_amount = total_amount_value

    @api.depends('bap_ids.sub_total', 'bap_ids.tax_ids')
    def compute_total_tax(self):
        for record in self:
            total_tax_value = sum(record.bap_ids.mapped('tax_amount'))
            record.total_tax = total_tax_value
    
    @api.depends('bap_ids.price_unit_po', 'bap_ids.qty')
    def compute_current_value(self):
        for record in self:
            total_current_value = sum(record.bap_ids.mapped('tax_amount'))
            record.total_tax = total_tax_value

    @api.depends('total_amount', 'total_tax')
    def compute_grand_total(self):
        for record in self:
            record.grand_total = record.total_amount + record.total_tax

    def action_reject(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        cek = False
        level=self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'wika.berita.acara.pembayaran')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level),
                 ('transaction_type', '=', self.po_id.transaction_type)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            print(approval_line_id)
            groups_id = approval_line_id.groups_id
            if groups_id:
                print(groups_id.name)
                for x in groups_id.users:
                    print ("kkkkkkkkkkkkkkk")
                    if level == 'Proyek' and x.project_id == self.project_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True

        if cek == True:
            action = {
                'name': ('Reject Reason'),
                'type': "ir.actions.act_window",
                'res_model': "reject.wizard",
                'view_type': "form",
                'target': 'new',
                'view_mode': "form",
                'context': {'groups_id': groups_id.id},
                'view_id': self.env.ref('wika_berita_acara_pembayaran.action_reject_wizard').id,
            }
            return action
        else:
            raise ValidationError('User Akses Anda tidak berhak Reject!')


    def assign_todo_first(self):
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'wika.berita.acara.pembayaran')], limit=1)
        for res in self:
            level=res.level
            first_user = False
            if level:
                approval_id = self.env['wika.approval.setting'].sudo().search(
                    [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',res.po_id.transaction_type)], limit=1)
                approval_line_id = self.env['wika.approval.setting.line'].search([
                    ('sequence', '=', 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                groups_id = approval_line_id.groups_id
                if groups_id:
                    for x in groups_id.users:
                        if level == 'Proyek' and x.project_id == res.project_id:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == res.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == res.department_id:
                            first_user = x.id
                print(first_user)
                #     # Createtodoactivity
                if first_user:
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': 4,
                        'res_model_id': model_id.id,
                        'res_id': res.id,
                        'user_id': first_user,
                        'date_deadline': fields.Date.today() + timedelta(days=2),
                        'state': 'planned',
                        'summary': f"Need Upload Document {model_id.name}!"
                    })

            # Get Document Setting
            document_list = []
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])

            if doc_setting_id:
                for document_line in doc_setting_id:
                    document_list.append((0, 0, {
                        'bap_id': res.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                res.document_ids = document_list
            else:
                raise AccessError(
                    "Either approval and/or document settings are not found. Please configure it first in the settings menu.")

    def action_submit(self):
        if not self.bap_ids:
            raise ValidationError('List BAP tidak boleh kosong. Mohon isi List BAP terlebih dahulu!')

        for record in self:
            if any(not line.document for line in record.document_ids):
                raise ValidationError('Document belum di unggah, mohon unggah file terlebih dahulu!')
        cek = False
        level=self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'wika.berita.acara.pembayaran')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level),
                 ('transaction_type', '=', self.po_id.transaction_type)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', 1),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            print(approval_line_id)
            groups_id = approval_line_id.groups_id
            if groups_id:
                print(groups_id.name)
                for x in groups_id.users:
                    if level == 'Proyek' and x.project_id == self.project_id and x.id == self._uid:
                        print ("ok")
                        cek = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True
                    print (cek)

        if cek == True:
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
                self.env['wika.bap.approval.line'].sudo().create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Submit Document',
                    'bap_id': self.id
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
                    print(self.step_approve)
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
                                [('model', '=', 'wika.berita.acara.pembayaran')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': """Need Approval Document BAP"""
                        })
        else:
            raise ValidationError('User Akses Anda tidak berhak Submit!')

    def action_approve(self):
        user = self.env['res.users'].search([('id','=',self._uid)], limit=1)
        documents_model = self.env['documents.document'].sudo()
        cek = False
        model_id = self.env['ir.model'].search([('model','=', 'wika.berita.acara.pembayaran')], limit=1)
        level=self.level
        if level:
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level),
                 ('transaction_type', '=', self.po_id.transaction_type)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu BAP tidak ditemukan. Silakan hubungi Administrator!')

            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            print(approval_line_id)
            groups_id = approval_line_id.groups_id
            if groups_id:
                print(groups_id.name)
                for x in groups_id.users:
                    if level == 'Proyek' and x.project_id == self.project_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id == self._uid:
                        cek = True
                    if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id == self._uid:
                        cek = True

        if cek == True:
            if approval_id.total_approve == self.step_approve:
                self.state = 'approved'
                self.env['wika.bap.approval.line'].create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Approved',
                    'bap_id': self.id
                })
                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'BAP')], limit=1)
                # print("TESTTTTTTTTTTTTTTTTTTTTT", folder_id)
                if folder_id:
                    facet_id = self.env['documents.facet'].sudo().search([
                        ('name', '=', 'Wika BAP'),
                        ('folder_id', '=', folder_id.id)
                    ], limit=1)
                    # print("TESTTTTTTTTTERRRRRRR", facet_id)
                    for doc in self.document_ids.filtered(lambda x: x.state in ('uploaded','rejected')):
                        doc.state = 'verified'
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
                                'purchase_id': self.po_id.id,
                            })
                if self.activity_ids:
                    for x in self.activity_ids.filtered(lambda x: x.status  != 'approved'):
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
                        if level == 'Proyek' and x.project_id == self.project_id:
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
                                [('model', '=', 'wika.berita.acara.pembayaran')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status': 'to_approve',
                            'summary': """Need Approval Document BAP"""
                        })
                        self.env['wika.bap.approval.line'].create({
                            'user_id': self._uid,
                            'groups_id': groups_id.id,
                            'date': datetime.now(),
                            'note': 'Verified',
                            'bap_id': self.id
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
            
    def action_cancel(self):
        self.write({'state': 'draft'})

    @api.onchange('po_id')
    def onchange_po(self):
        self.partner_id = self.po_id.partner_id.id

    def unlink(self):
        for record in self:
            if record.state in ('uploaded', 'approved'):
                raise ValidationError('Tidak dapat menghapus ketika status Berita Acara Pembayaran (BAP) dalam keadaan Upload atau Approve')
            if record.state=='draft' and record.activity_ids:
                record.activity_ids.unlink()
        return super(WikaBeritaAcaraPembayaran, self).unlink()

    def action_print_bap(self):
        return self.env.ref('wika_berita_acara_pembayaran.report_wika_berita_acara_pembayaran_action').report_action(self)

    # @api.onchange('end_date')
    # def _check_contract_expiry_on_save(self):
    #     if self.end_date and self.end_date < fields.Date.today():
    #         raise UserError(_("Tanggal akhir kontrak PO sudah kadaluarsa. Silakan perbarui kontrak segera!"))
    #
    # @api.model
    # def create(self, values):
    #     record = super(WikaBeritaAcaraPembayaran, self).create(values)
    #     record._check_contract_expiry_on_save()
    #     return record
    #
    # def write(self, values):
    #     super(WikaBeritaAcaraPembayaran, self).write(values)
    #     self._check_contract_expiry_on_save()
    #     return True

class WikaBeritaAcaraPembayaranLine(models.Model):
    _name = 'wika.berita.acara.pembayaran.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    picking_id = fields.Many2one('stock.picking', string='NO GR/SES')
    purchase_line_id= fields.Many2one('purchase.order.line', string='Purchase Line')
    unit_price_po = fields.Monetary(string='Price Unit PO')
    # account_move_line_id = fields.Many2one('account.move.line', string='Move Line')
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Integer(string='Quantity')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    tax_ids = fields.Many2many('account.tax', string='Tax')
    currency_id = fields.Many2one('res.currency', string='Currency')
    unit_price = fields.Monetary(string='Unit Price')
    sub_total = fields.Monetary(string='Subtotal' , compute= 'compute_sub_total')
    tax_amount = fields.Monetary(string='Tax Amount', compute='compute_tax_amount')
    current_value = fields.Monetary(string='Current Value', compute='_compute_current_value')

    @api.depends('tax_ids', 'sub_total')
    def compute_sub_total(self):
        for record in self:
            tax_rate = sum(record.tax_ids.mapped('amount')) / 100  # Assuming tax amount is in percentage
            record.sub_total = record.sub_total + (record.sub_total * tax_rate)

    @api.depends('tax_ids', 'sub_total')
    def compute_tax_amount(self):
        for record in self:
            tax_amount_value = sum(record.tax_ids.mapped('amount')) * record.sub_total / 100
            record.tax_amount = tax_amount_value

    @api.depends('qty', 'unit_price')
    def compute_sub_total(self):
        for record in self:
            record.sub_total = record.qty * record.unit_price

    @api.constrains('picking_id')
    def _check_picking_id(self):
        for record in self:
            if not record.picking_id:
                raise ValidationError('Field "NO GR/SES" harus diisi. Tidak boleh kosong!')

    @api.depends('unit_price_po', 'qty')
    def _compute_current_value(self):
        for record in self:
            record.current_value = record.qty * record.unit_price_po

class WikaBabDocumentLine(models.Model):
    _name = 'wika.bap.document.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(string="Upload File", attachment=True, store=True, required=True)
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

class WikaBabApprovalLine(models.Model):
    _name = 'wika.bap.approval.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    groups_id = fields.Many2one('res.groups', string='Groups', readonly=True)
    date = fields.Datetime('Date', readonly=True)
    note = fields.Char('Note', readonly=True)

class WikaPriceCutLine(models.Model):
    _name = 'wika.bap.pricecut.line'
    _description = 'Wika Price Cut Line'

    po_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    product_id = fields.Many2one('product.product', string='Product')
    amount = fields.Float(string='Amount')

