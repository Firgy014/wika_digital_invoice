from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import AccessError, ValidationError
from odoo.exceptions import UserError
import requests
import json
from datetime import datetime, timedelta

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    is_visible_button = fields.Boolean('Show Operation Buttons', default=True)
    branch_id = fields.Many2one('res.branch', string='Divisi', required=True)
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    state = fields.Selection(selection_add=[
        ('po', 'PO'),
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ])
    po_type = fields.Char(string='Purchasing Doc Type')
    begin_date = fields.Date(string='Tgl Mulai Kontrak')
    end_date = fields.Date(string='Tgl Akhir Kontrak')
    document_ids = fields.One2many('wika.po.document.line', 'purchase_id', string='Purchase Order Document Lines')
    history_approval_ids = fields.One2many('wika.po.approval.line', 'purchase_id',
                                           string='Purchase Order Approval Lines')
    sap_doc_number = fields.Char(string='Nomor Kontrak')
    step_approve = fields.Integer(string='Step Approve',default=1)
    picking_count = fields.Integer(string='Total GR/SES', compute='_compute_picking_count')
    kurs = fields.Float(string='Kurs')
    currency_name = fields.Char(string='Currency Name', related='currency_id.name', readonly=False)
    signatory_name = fields.Char(string='Nama Penanda Tangan')
    vendor_signatory_name = fields.Char(string='Nama Penanda Tangan Vendor')
    position = fields.Char(string='Jabatan')
    vendor_position = fields.Char(string='Jabatan Vendor')
    address = fields.Char(string='Alamat')
    job = fields.Char(string='Pekerjaan')
    price_cut_ids = fields.One2many('wika.po.pricecut.line', 'purchase_id', string='Other Price Cut')
    active = fields.Boolean(string='Active',default=True)
    tgl_create_sap= fields.Date(string='Tgl Create SAP')
    check_biro = fields.Boolean(compute="_cek_biro")
    transaction_type = fields.Selection([
        ('BTL', 'BTL'),
        ('BL', 'BL'),
    ],compute="cek_transaction_type",store=True)
    level = fields.Selection([
        ('Proyek', 'Proyek'),
        ('Divisi Operasi', 'Divisi Operasi'),
        ('Divisi Fungsi', 'Divisi Fungsi'),
        ('Pusat', 'Pusat')
    ], string='Level',compute='_compute_level')

    @api.depends('project_id','branch_id','department_id')
    def _compute_level(self):
        for res in self:
            if res.project_id:
                level = 'Proyek'
            elif res.branch_id and not res.department_id and not res.project_id:
                level = 'Divisi Operasi'
            elif res.branch_id and res.department_id and not res.project_id:
                level = 'Divisi Fungsi'
            res.level=level


    @api.constrains('begin_date', 'end_date')
    def _check_end_date_greater_than_begin_date(self):
        for record in self:
            if record.end_date and record.begin_date:
                if record.end_date < record.begin_date:
                    raise ValidationError("End date cannot be earlier than begin date.")

    @api.onchange('begin_date', 'end_date')
    def _onchange_dates(self):
        if self.end_date and self.begin_date:
            if self.end_date < self.begin_date:
                self.end_date = False
                raise ValidationError("End date cannot be earlier than begin date.")



    def init(self):
        self.env.cr.execute("DELETE FROM purchase_order WHERE state NOT IN ('po', 'uploaded', 'approved')")

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

    @api.depends('order_line.product_id.default_code')
    def cek_transaction_type(self):
        for x in self.order_line:
            if x.product_id.default_code[0] in ('A','C','D','E'):
                self.transaction_type='BL'
            else:
                self.transaction_type = 'BTL'

    # def get_gr(self):
    #     url_config = self.env['wika.integration'].search([('name', '=', 'URL GR')], limit=1).url
    #     print ("-------------------------------")
    #     print (url_config)
    #     headers = {
    #         'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
    #         'Content-Type': 'application/json'
    #     }
    #     payload = json.dumps({
    #         "IV_EBELN": "%s",
    #         "IW_CPUDT_RANGE": {
    #             "CPUDT_LOW": "%s",
    #             "CPUTM_LOW": "00:00:00",
    #             "CPUDT_HIGH": "2025-12-31",
    #             "CPUTM_HIGH": "23:59:59"
    #         }
    #     }) % (self.name, self.begin_date)
    #     payload = payload.replace('\n', '')
    #     print(payload)
    #     try:
    #         response = requests.request("GET", url_config, data=payload, headers=headers)
    #         txt = json.loads(response.text)
    #     except:
    #         raise UserError(_("Connection Failed. Please Check Your Internet Connection."))
    #     if txt['DATA']:
    #         txt_data = txt['DATA']
    #         vals = []
    #         vals_header = []
    #         for hasil in txt_data:
    #             print(hasil)
    #             po_exist  = self.env['purchase.order'].sudo().search([
    #                 ('name', '=' ,hasil['PO_NUMBER'])] ,limit=1)
    #             if po_exist:
    #                 prod = self.env['product.product'].sudo().search([
    #                     ('default_code', '=', hasil['MATERIAL'])], limit=1)
    #                 qty = float(hasil['QUANTITY']) * 100
    #                 uom = self.env['uom.uom'].sudo().search([
    #                     ('name', '=', hasil['ENTRY_UOM'])], limit=1)
    #                 if po_exist.po_type=='BARANG':
    #                     tipe_gr='gr'
    #                 else:
    #                     tipe_gr = 'ses'
    #                 if not uom:
    #                     uom = self.env['uom.uom'].sudo().create({
    #                         'name': hasil['ENTRY_UOM'], 'category_id': 1})
    #                 vals.append((0, 0, {
    #                     'product_id': prod.id if prod else False,
    #                     'quantity_done': qty,
    #                     'product_uom': uom.id,
    #                     'location_id': 4,
    #                     'location_dest_id': 8,
    #                     'name':hasil['MAT_DOC']
    #                 }))
    #             #     vals_header.append((0, 0, {
    #             #         'name': hasil['MAT_DOC'],
    #             #         'po_id': po_exist.id,
    #             #         'project_id': po_exist.project_id.id,
    #             #         'branch_id': po_exist.branch_id.id,
    #             #         'department_id': po_exist.department_id.id,
    #             #         'scheduled_date':hasil['DOC_DATE']
    #             #     }))
    #             matdoc=hasil['MAT_DOC']
    #             docdate = hasil['DOC_DATE']
    #             gr_type=hasil['MATERIAL']
    #         if vals:
    #             print("ppppppppppppppppppppp")
    #             picking_create = self.env['stock.picking'].sudo().create({
    #                 'name': matdoc,
    #                 'po_id': po_exist.id,
    #                 'project_id': po_exist.project_id.id,
    #                 'branch_id': po_exist.branch_id.id,
    #                 'department_id': po_exist.department_id.id if po_exist.department_id.id else False,
    #                 'scheduled_date':docdate,
    #                 'partner_id':po_exist.partner_id.id,
    #                 'location_id':4,
    #                 'location_dest_id':8,
    #                 'picking_type_id':1,
    #                 'move_ids':vals,
    #                 'pick_type':tipe_gr,
    #                 #'move_ids_without_package':vals,
    #                 'company_id':1,
    #                 'state':'waits'
    #             })
    #         else:
    #             raise UserError(_("Data GR Tidak Tersedia di PO TERSEBUT!"))
    #
    #     else:
    #         raise UserError(_("Data GR Tidak Tersedia!"))

    def get_gr(self):
        url_config = self.env['wika.integration'].search([('name', '=', 'URL GR')], limit=1).url
        print("-------------------------------")
        print(url_config)
        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "IV_EBELN": "%s",
            "IW_CPUDT_RANGE": {
                "CPUDT_LOW": "%s",
                "CPUTM_LOW": "00:00:00",
                "CPUDT_HIGH": "2025-12-31",
                "CPUTM_HIGH": "23:59:59"
            }
        }) % (self.name, self.begin_date)
        payload = payload.replace('\n', '')
        print(payload)
        try:
            response = requests.request("GET", url_config, data=payload, headers=headers)
            txt = json.loads(response.text)
        except:
            raise UserError(_("Connection Failed. Please Check Your Internet Connection."))
        if self.po_type != 'JASA':
            if txt['DATA']:
                txt_data = sorted(txt['DATA'], key=lambda x: x["MAT_DOC"])
                mat_doc_dict = {}
                for hasil in txt_data:
                    mat_doc = hasil["MAT_DOC"]
                    if mat_doc in mat_doc_dict:
                        # Append the item to the existing list
                        mat_doc_dict[mat_doc].append(hasil)
                    else:
                        # Create a new list with the current item
                        mat_doc_dict[mat_doc] = [hasil]
                for mat_doc, items in mat_doc_dict.items():
                    print(f"MAT_DOC: {mat_doc}")
                    print("hehe")
                    vals = []
                    for item in items:
                        # if item['REVERSE']=='X':
                        #     active=False
                        # else:
                        #     active = True
                        prod = self.env['product.product'].sudo().search([
                                    ('default_code', '=', item['MATERIAL'])], limit=1)
                        qty = float(item['QUANTITY']) * 100
                        uom = self.env['uom.uom'].sudo().search([
                                    ('name', '=', item['ENTRY_UOM'])], limit=1)
                        if not uom:
                            uom = self.env['uom.uom'].sudo().create({
                                'name': hasil['ENTRY_UOM'], 'category_id': 1})
                        po_line= self.env['purchase.order.line'].sudo().search([
                                 ('order_id', '=' ,self.id),('sequence','=',item['PO_ITEM'])] ,limit=1)
                        vals.append((0, 0, {
                            'sequence':item['MATDOC_ITM'],
                            'product_id': prod.id if prod else False,
                            'quantity_done': float(item['QUANTITY']),
                            'product_uom_qty': float(item['QUANTITY']),
                            'product_uom': uom.id,
                            #'active':active,
                            'state':'waits',
                            'location_id': 4,
                            'location_dest_id': 8,
                            'purchase_line_id':po_line.id,
                            'name': hasil['PO_NUMBER']
                        }))
                        print(item['DOC_DATE'])
                        docdate = hasil['DOC_DATE']
                    print(vals)
                    if vals:
                        print("ppppppppppppppppppppp")
                        picking_create = self.env['stock.picking'].sudo().create({
                            'name': mat_doc,
                            'po_id': self.id,
                            'purchase_id':self.id,
                            'project_id': self.project_id.id,
                            'branch_id': self.branch_id.id,
                            'department_id': self.department_id.id if self.department_id.id else False,
                            'scheduled_date': docdate,
                            'start_date': docdate,
                            'partner_id': self.partner_id.id,
                            'location_id': 4,
                            'location_dest_id': 8,
                            'picking_type_id': 1,
                            'move_ids': vals,
                            'pick_type': 'gr',
                            #'move_ids_without_package':vals,
                            'company_id': 1,
                            'state': 'waits'
                        })
                    else:
                        raise UserError(_("Data GR Tidak Tersedia di PO TERSEBUT!"))
            else:
                raise UserError(_("Data GR Tidak Tersedia!"))
        else:
            if txt['DATA']:
                txt_data = sorted(txt['DATA'], key=lambda x: x["MAT_DOC"])
                mat_doc_dict = {}
                ses_number_dict = {}
                for hasil in txt_data:
                    mat_doc = hasil["MAT_DOC"]
                    ses_number = hasil["SES_NUMBER"]
                    if ses_number in ses_number_dict:
                        # Append the item to the existing list
                        ses_number_dict[ses_number].append(hasil)
                    else:
                        # Create a new list with the current item
                        ses_number_dict[ses_number] = [hasil]
                for ses_number, items in ses_number_dict.items():
                    print(f"SES_DOC: {ses_number}")
                    print("hehe")
                    vals = []
                    for item in items:
                        # if item['REVERSE'] == 'X':
                        #     active = False
                        # else:
                        #     active = True
                        prod = self.env['product.product'].sudo().search([
                            ('default_code', '=', item['MATERIAL'])], limit=1)
                        qty = float(item['QUANTITY']) * 100
                        uom = self.env['uom.uom'].sudo().search([
                            ('name', '=', item['ENTRY_UOM'])], limit=1)
                        if not uom:
                            uom = self.env['uom.uom'].sudo().create({
                                'name': hasil['ENTRY_UOM'], 'category_id': 1})
                        po_line = self.env['purchase.order.line'].sudo().search([
                            ('order_id', '=', self.id), ('sequence', '=', item['PO_ITEM'])], limit=1)
                        vals.append((0, 0, {
                            'sequence': item['MATDOC_ITM'],
                            'product_id': prod.id if prod else False,
                            'quantity_done': float(item['QUANTITY']),
                            'product_uom_qty': float(item['QUANTITY']),
                            'product_uom': uom.id,
                            #'active': active,
                            'state':'waits',
                            'location_id': 4,
                            'location_dest_id': 8,
                            'purchase_line_id': po_line.id,
                            'name': hasil['PO_NUMBER']
                        }))
                        print(item['DOC_DATE'])
                        docdate = hasil['DOC_DATE']
                        matdoc = item['MAT_DOC']
                    print(vals)
                    if vals:
                        print("ppppppppppppppppppppp")
                        picking_create = self.env['stock.picking'].sudo().create({
                            'name': ses_number,
                            'po_id': self.id,
                            'purchase_id': self.id,
                            'project_id': self.project_id.id,
                            'branch_id': self.branch_id.id,
                            'department_id': self.department_id.id if self.department_id.id else False,
                            'scheduled_date': docdate,
                            'start_date': docdate,
                            'partner_id': self.partner_id.id,
                            'location_id': 4,
                            'location_dest_id': 8,
                            'picking_type_id': 1,
                            'move_ids': vals,
                            'pick_type': 'ses',
                            'origin':matdoc,
                            #'move_ids_without_package':vals,
                            'company_id': 1,
                            'state': 'waits'
                        })
                    else:
                        raise UserError(_("Data GR Tidak Tersedia di PO TERSEBUT!"))

            else:
                raise UserError(_("Data GR Tidak Tersedia!"))

    def assign_todo_first(self):
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'purchase.order')], limit=1)
        for res in self:
            level=res.level
            first_user = False
            if level:
                approval_id = self.env['wika.approval.setting'].sudo().search(
                    [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',res.transaction_type)], limit=1)
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
                        'purchase_id': res.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                res.document_ids = document_list
            else:
                raise AccessError(
                    "Either approval and/or document settings are not found. Please configure it first in the settings menu.")

    @api.model_create_multi
    def create(self, vals_list):
        model_model = self.env['ir.model'].sudo()
        for vals in vals_list:
            res = super(PurchaseOrderInherit, self).create(vals)
            res.assign_todo_first()
        return res

    def action_approve(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        documents_model = self.env['documents.document'].sudo()
        cek = False
        model_id = self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
        level = self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',self.transaction_type)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu Purchase Orders tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
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
            if approval_id.total_approve == self.step_approve:
                self.state = 'approved'
                self.env['wika.po.approval.line'].create({
                    'user_id': self._uid,
                    'groups_id': groups_id.id,
                    'date': datetime.now(),
                    'note': 'Approved',
                    'purchase_id': self.id
                })
                folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'PO')], limit=1)
                if folder_id:
                    facet_id = self.env['documents.facet'].sudo().search([
                        ('name', '=', 'Documents'),
                        ('folder_id', '=', folder_id.id)
                    ], limit=1)
                    for doc in self.document_ids.filtered(lambda x: x.state in ('uploaded','rejected')):
                        doc.state = 'verified'
                        attachment_id = self.env['ir.attachment'].sudo().create({
                            'name': doc.filename,
                            'datas': doc.document,
                            'res_model': 'documents.document',
                        })
                        if attachment_id:
                            tag=self.env['documents.tag'].sudo().search([
                                    ('facet_id', '=',facet_id.id),
                                    ('name', '=', doc.document_id.name)
                                ], limit=1)
                            documents_model.create({
                                'attachment_id': attachment_id.id,
                                'folder_id': folder_id.id,
                                'tag_ids': tag.ids,
                                'partner_id': doc.purchase_id.partner_id.id,
                                'purchase_id': self.id,
                                'is_po_doc': True
                            })
                if self.activity_ids:
                    for x in self.activity_ids.filtered(lambda x: x.status != 'approved'):
                        if x.user_id.id == self._uid:
                            print(x.status)
                            x.status = 'approved'
                            x.action_done()
            else:
                first_user=False
                # Createtodoactivity
                groups_line_next = self.env['wika.approval.setting.line'].search([
                    ('level', '=', level),
                    ('sequence', '=', self.step_approve+1),
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
                                [('model', '=', 'purchase.order')], limit=1).id,
                            'res_id': self.id,
                            'user_id': first_user,
                            'date_deadline': fields.Date.today() + timedelta(days=2),
                            'state': 'planned',
                            'status':'to_approve',
                            'summary': """Need Approval Document PO"""
                        })
                        self.env['wika.po.approval.line'].create({
                            'user_id': self._uid,
                            'groups_id': groups_id.id,
                            'date': datetime.now(),
                            'note': 'Verified',
                            'purchase_id': self.id
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
        level=self.level
        if level:
            model_id = self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',self.transaction_type)], limit=1)
            if not approval_id:
                raise ValidationError(
                    'Approval Setting untuk menu Purchase Orders tidak ditemukan. Silakan hubungi Administrator!')
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', self.step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)

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
            action = {
                'name': ('Reject Reason'),
                'type': "ir.actions.act_window",
                'res_model': "po.reject.wizard",
                'view_type': "form",
                'target': 'new',
                'view_mode': "form",
                'context': {'groups_id': groups_id.id},
                'view_id': self.env.ref('wika_purchase.po_reject_wizard_form').id,
            }
            return action
        else:
            raise ValidationError('User Akses Anda tidak berhak Reject!')

    def action_submit(self):
        if self.signatory_name and self.vendor_signatory_name and self.position and self.vendor_position and self.end_date and self.sap_doc_number:
            if self.document_ids:
                for doc_line in self.document_ids:
                    if doc_line.document == False:
                        raise ValidationError('Anda belum mengunggah dokumen yang diperlukan!')
                cek = False
                level=self.level

                if level:
                    model_id = self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
                    approval_id = self.env['wika.approval.setting'].sudo().search(
                        [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',self.transaction_type)], limit=1)
                    print('approval_idapproval_idapproval_id')
                    if not approval_id:
                        raise ValidationError(
                            'Approval Setting untuk menu Purchase Orders tidak ditemukan. Silakan hubungi Administrator!')
                    approval_line_id = self.env['wika.approval.setting.line'].search([
                        ('sequence', '=', 1),
                        ('approval_id', '=', approval_id.id)
                    ], limit=1)
                    print(approval_line_id)
                    groups_id = approval_line_id.groups_id
                    if groups_id:
                        print(groups_id.name)
                        for x in groups_id.users:
                            if level == 'Proyek' and x.project_id == self.project_id and x.id== self._uid:
                                cek = True
                            if level == 'Divisi Operasi' and x.branch_id == self.branch_id and x.id== self._uid:
                                cek = True
                            if level == 'Divisi Fungsi' and x.department_id == self.department_id and x.id== self._uid:
                                cek = True
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
                    self.env['wika.po.approval.line'].sudo().create({
                        'user_id': self._uid,
                        'groups_id': groups_id.id,
                        'date': datetime.now(),
                        'note': 'Submit Document',
                        'purchase_id': self.id
                    })
                    print(self.step_approve)
                    groups_line = self.env['wika.approval.setting.line'].search([
                        ('level', '=', level),
                        ('sequence', '=', self.step_approve),
                        ('approval_id', '=', approval_id.id)
                    ], limit=1)
                    print("groups", groups_line)
                    groups_id_next = groups_line.groups_id
                    if groups_id_next:
                        print (groups_id_next.name)
                        for x in groups_id_next.users:
                            if level == 'Proyek' and x.project_id == self.project_id:
                                first_user = x.id
                            if level == 'Divisi Operasi' and x.branch_id == self.branch_id:
                                first_user = x.id
                            if level == 'Divisi Fungsi' and x.department_id == self.department_id:
                                first_user = x.id
                        print (first_user)
                        if first_user:
                            self.env['mail.activity'].sudo().create({
                                'activity_type_id': 4,
                                'res_model_id': self.env['ir.model'].sudo().search(
                                    [('model', '=', 'purchase.order')], limit=1).id,
                                'res_id': self.id,
                                'user_id': first_user,
                                'date_deadline': fields.Date.today() + timedelta(days=2),
                                'state': 'planned',
                                'status': 'to_approve',
                                'summary': """Need Approval Document PO"""
                            })

            else:
                raise ValidationError('User Akses Anda tidak berhak Submit!')

        else:
            raise ValidationError('Mohon untuk diisi terlebih dahulu Nama Penanda Tangan, Jabatan, Nama Penanda Tangan Vendor, Jabatan Vendor, Tgl Akhir Kontrak dan Nomor Kontrak.')

    def get_picking(self):
        self.ensure_one()
        view_tree_id = self.env.ref("wika_inventory.stock_picking_tree_wika", raise_if_not_found=False)
        view_form_id = self.env.ref("wika_inventory.stock_picking_form_wika", raise_if_not_found=False)

        return {
            'name': _('GR/SES'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_ids': [(view_tree_id, 'tree'), (view_form_id, 'form')],
            'res_id': self.id,
            'domain': [('po_id', '=', self.id)],  
            'context': {'default_po_id': self.id},
        }

    def _compute_picking_count(self):
        for record in self:
            record.picking_count = self.env['stock.picking'].search_count(
                [('po_id', '=', record.id)])

class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    unit_price_idr = fields.Float(string='Unit Price IDR')
    subtotal_idr = fields.Float(string='Subtotal IDR')
    active      = fields.Boolean(string='Active',default=True)

class PurchaseOrderDocumentLine(models.Model):
    _name = 'wika.po.document.line'
    _description = 'List Document PO'

    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(attachment=True, store=True, string='Upload File')
    filename = fields.Char(string='File Name')
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], string='Status')

    @api.onchange('document')
    def onchange_document_upload(self):
        if self.document:
            if self.filename and not self.filename.lower().endswith('.pdf'):
                self.document = False
                self.filename = False
                self.state = 'waiting'
                raise ValidationError('Tidak dapat mengunggah file selain ekstensi PDF!')
            elif self.filename.lower().endswith('.pdf'):
                self.state = 'uploaded'

        else:
            self.document = False
            self.filename = False
            self.state = 'waiting'

    # @api.constrains('document', 'filename')
    # def _check_attachment_format(self):
    #     for record in self:
    #         if record.filename and not record.filename.lower().endswith('.pdf'):
    #             # self.document = False
    #             # self.state = 'waiting'
    #             raise ValidationError('Tidak dapat mengunggah file selain ekstensi PDF!')

class PurchaseOrderApprovalLine(models.Model):
    _name = 'wika.po.approval.line'
    _description = 'History Approval PO'

    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')

class PriceCutLine(models.Model):
    _name = 'wika.po.pricecut.line'
    _description = 'Price Cut Line'
    
    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    product_id = fields.Many2one('product.product', string='Product')
    persentage_amount = fields.Float(string='% Amount')
    amount = fields.Float(string='Amount')
