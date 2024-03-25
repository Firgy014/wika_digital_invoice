# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError, Warning,AccessError
import logging, json
_logger = logging.getLogger(__name__)

class wika_get_po(models.Model):
    _name = 'wika.get.po'
    _description='Wika Get Integration'

    profit_center = fields.Char(string="Profit Center")
    name = fields.Char(string="Nomor PO")
    jenis = fields.Char(string="Jenis")
    po_plant = fields.Char(string="PO Plant")
    co_code = fields.Char(string="Co Code")
    status=fields.Char(string='Status')
    tgl_create_sap = fields.Char(string='Date')
    def get_po(self):
        url_config = self.env['wika.integration'].search([('name', '=', 'URL PO')], limit=1)
        url= url_config.url+'services/auth'
        url_get_po = url_config.url + 'services/getposap'
        #print (url)
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "entitas": "FMS",
            "skey": "OAZvRmB7HKDdDkKF29DXZwgSmlv9KqQWZNDWV51SACAbhnOvuA1AvZf5FnIBrLxC"
        })
        payload =payload.replace('\n', '')
        try:
            # 1. Get W-KEY TOKEN
            response = requests.request("POST", url, data=payload, headers=headers)
            w_key =(response.headers['w-key'])
            csrf = {'w-access-token': str(w_key)}
            headers.update(csrf)
            #print (headers)
            if self.tgl_create_sap:
                tgl_create_sap=self.tgl_create_sap
            else:
                tgl_create_sap=""
            if self.name:
                no_po=self.name
            else:
                no_po=""
            payload_2 = json.dumps({"profit_center" : "%s",
            "po_doc" : "%s",
            "po_jenis" : "",
            "po_dcdat" : "",
            "po_crdate": "",
            "po_plant" : "A000",
            "co_code" : "A000",
            "po_del" : "",
            "poitem_del" : "",
            "incmp_cat" : ""
        }) % (self.profit_center, no_po, tgl_create_sap)
            payload_2 = payload_2.replace('\n', '')
            _logger.info(payload_2)
            response_2 = requests.request("POST", url_get_po, data=payload_2, headers=headers)
            txt = json.loads(response_2.text)
        except:
            pass
            #raise UserError(_("Connection Failed. Please Check Your Internet Connection."))
        if txt['data']:
            txt_data = txt['data']
            if isinstance(txt_data, list):
                for data in txt_data:
                    vals=[]
                    potongan=[]
                    if data['po_del']=='C':
                        po= self.env['purchase.order'].sudo().search([
                                        ('name', '=', data['po_doc']),('tgl_create_sap','=',data['po_crdat']),('state','!=','cancel')], limit=1)
                        if po:
                            po.write({'state': 'cancel', 'active': False})
                    else:
                        po = self.env['purchase.order'].sudo().search([
                            ('name', '=', data['po_doc']), ('tgl_create_sap', '=', data['po_crdat']),
                            ('state', '!=', 'cancel')], limit=1)
                        if not po:
                            dp= float(data['dp_amt'])
                            retensi=float(data['ret_pc'])
                            if 'pay_terms' in txt_data and txt_data['pay_terms'] != '':
                                payment_term = self.env['account.payment.term'].sudo().search([
                                    ('name', '=', txt_data['pay_terms'])], limit=1)
                            if dp > 0:
                                prod = self.env['product.product'].sudo().search([
                                    ('name', '=', 'DP')], limit=1)
                                if not prod:
                                    prod = self.env['product.product'].sudo().create({
                                        'name': 'DP'})
                                potongan.append((0, 0, {
                                    'product_id': prod.id,
                                    'amount': dp,
                                }))
                            if retensi >0:
                                prod = self.env['product.product'].sudo().search([
                                    ('name', '=', 'RETENSI')], limit=1)
                                if not prod:
                                    prod = self.env['product.product'].sudo().create({
                                        'name': 'RETENSI'})
                                potongan.append((0, 0, {
                                    'product_id': prod.id,
                                    'persentage_amount':retensi
                                }))
                            for hasil in data['isi']:
                                seq = float(hasil['po_no'])
                                line_active = True
                                state = 'po'

                                prod = self.env['product.product'].sudo().search([
                                    ('default_code', '=', hasil['prd_no'])], limit=1)

                                qty = float(data['po_qty'])
                                print("qty awalfffffffffffffff-------------------------------",qty)
                                if txt_data['po_jenis'] == 'JASA':
                                    price = float(data['po_price']) / qty
                                else:
                                    price = float(data['po_price'])
                                if not prod:
                                    return "Material/Service  : %s tidak ditemukan" % (hasil['prd_no'])
                                tax = self.env['account.tax'].sudo().search([
                                                 ('name', '=', hasil['tax_code'])], limit=1)
                                if not tax:
                                    return "Kode Pajak  : %s tidak ditemukan" % hasil['MWSKZ']
                                curr = self.env['res.currency'].sudo().search([
                                    ('name', '=', data['curr'])], limit=1)
                                if not curr:
                                    continue
                                vendor = self.env['res.partner'].sudo().search([
                                                ('sap_code', '=', data['vendor'])], limit=1)
                                if not vendor:
                                    continue
                                    # return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
                                uom = self.env['uom.uom'].sudo().search([
                                    ('name', '=', hasil['po_uom'])], limit=1)
                                if not uom:
                                    uom = self.env['uom.uom'].sudo().create({
                                        'name': hasil['po_uom'], 'category_id': 1})
                                project = self.env['project.project'].sudo().search([
                                    ('sap_code', '=', data['prctr']), ('company_id', '=', 1)], limit=1)
                                if project:
                                    profit_center = project.id
                                    branch_id = project.branch_id.id
                                    department_id = None
                                if not project:
                                    branch = self.env['res.branch'].sudo().search([
                                        ('sap_code', '=', data['prctr']), ('company_id', '=', 1)], limit=1)
                                    if branch and branch.biro == True:
                                        department_id = branch.id
                                        branch_id = branch.parent_id.id
                                        profit_center = None
                                    if branch and branch.biro == False:
                                        department_id = None
                                        branch_id = branch.id
                                        profit_center = None
                                    if not branch:
                                        return "Kode Profit Center : %s tidak ditemukan" % data['prctr']
                                if hasil['poitem_del'] == 'L':
                                    line_active = False
                                vals.append((0, 0, {
                                         'sequence': int(seq),
                                         'product_id': prod.id if prod else False,
                                         'product_qty': qty,
                                         'product_uom': uom.id,
                                         'price_unit': price,
                                        'active':line_active,
                                         'taxes_id': [(6, 0, [x.id for x in tax])]

                                     }))
                        else:
                            for hasil in data['isi']:
                                seq = float(hasil['po_no'])
                                po_line = self.env['purchase.order.line'].sudo().search([
                                    ('sequence', '=', int(seq))], limit=1)
                                if po_line and hasil['poitem_del'] == 'L':
                                    po_line.write({'active': False})

                        if not vals:
                            continue
                        else:
                            po_create = self.env['purchase.order'].sudo().create({
                                'name': data['po_doc'],
                            'payment_term_id':payment_term.id if payment_term else False,

                                'partner_id': vendor.id if vendor else False,
                                'project_id': profit_center,
                                'branch_id': branch_id,
                                'department_id': department_id,
                                'order_line': vals,
                                'price_cut_ids':potongan,
                                'currency_id': curr.id,
                                'begin_date': data['po_dcdat'],
                                'po_type': data['po_jenis'],
                                'state': state,
                                'tgl_create_sap': data['po_crdat']

                            })
                            po_create.get_gr()
            else:
                vals = []
                potongan = []
                if txt_data['po_del'] == 'C':
                    po = self.env['purchase.order'].sudo().search([
                        ('name', '=', txt_data['po_doc']), ('tgl_create_sap', '=', txt_data['po_crdat']),
                         ('state', '!=', 'cancel')], limit=1)
                    if po:
                        po.write({'state': 'cancel', 'active': False})
                else:
                    po = self.env['purchase.order'].sudo().search([
                        ('name', '=', txt_data['po_doc']), ('tgl_create_sap', '=', txt_data['po_crdat']),
                         ('state', '!=', 'cancel')], limit=1)
                    if not po:
                        dp = float(txt_data['dp_amt'])
                        retensi = float(txt_data['ret_pc'])
                        if txt_data['pay_terms']!='':
                            payment_term = self.env['account.payment.term'].sudo().search([
                                ('name', '=', txt_data['pay_terms'])], limit=1)


                        if dp > 0:
                            prod = self.env['product.product'].sudo().search([
                                ('name', '=', 'DP')], limit=1)
                            if not prod:
                                prod = self.env['product.product'].sudo().create({
                                    'name': 'DP'})
                            potongan.append((0, 0, {
                                'product_id': prod.id,
                                'amount': dp,
                            }))
                        if retensi > 0:
                            prod = self.env['product.product'].sudo().search([
                                ('name', '=', 'RETENSI')], limit=1)
                            if not prod:
                                prod = self.env['product.product'].sudo().create({
                                    'name': 'RETENSI'})
                            potongan.append((0, 0, {
                                'product_id': prod.id,
                                'persentage_amount': retensi
                            }))
                        for data in txt_data['isi']:
                            seq = float(data['po_no'])
                            line_active=True

                            state = 'po'

                            prod = self.env['product.product'].sudo().search([
                                ('default_code', '=', data['prd_no'])], limit=1)
                            qty = float(data['po_qty'])
                            if txt_data['po_jenis'] == 'JASA':
                                price = float(data['po_price'])/qty
                            else:
                                price = float(data['po_price'])
                            if not prod:
                                return "Material/Service  : %s tidak ditemukan" % (data['prd_no'])
                            tax = self.env['account.tax'].sudo().search([
                                             ('name', '=', data['tax_code'])], limit=1)
                            if not tax:
                                return "Kode Pajak  : %s tidak ditemukan" % data['MWSKZ']
                            curr = self.env['res.currency'].sudo().search([
                                ('name', '=', txt_data['curr'])], limit=1)
                            if not curr:
                                continue
                            vendor = self.env['res.partner'].sudo().search([
                                            ('sap_code', '=', txt_data['vendor'])], limit=1)
                            if not vendor:
                                continue
                                # return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
                            uom = self.env['uom.uom'].sudo().search([
                                ('name', '=', data['po_uom'])], limit=1)
                            if not uom:
                                uom = self.env['uom.uom'].sudo().create({
                                    'name': data['po_uom'], 'category_id': 1})
                            project = self.env['project.project'].sudo().search([
                                ('sap_code', '=', txt_data['prctr']), ('company_id', '=', 1)], limit=1)
                            if project:
                                profit_center = project.id
                                branch_id = project.branch_id.id
                                department_id = None
                            if not project:
                                branch = self.env['res.branch'].sudo().search([
                                    ('sap_code', '=', txt_data['prctr']), ('company_id', '=', 1)], limit=1)
                                if branch and branch.biro == True:
                                    department_id = branch.id
                                    branch_id = branch.parent_id.id
                                    profit_center = None
                                if branch and branch.biro == False:
                                    department_id = None
                                    branch_id = branch.id
                                    profit_center = None
                                if not branch:
                                    return "Kode Profit Center : %s tidak ditemukan" % txt_data['prctr']
                            if data['poitem_del'] == 'L':
                                line_active=False
                            vals.append((0, 0, {
                                     'sequence': int(seq),
                                     'product_id': prod.id if prod else False,
                                     'product_qty': qty,
                                     'product_uom': uom.id,
                                     'price_unit': price,
                                      'active':line_active,
                                     'taxes_id': [(6, 0, [x.id for x in tax])]

                                 }))
                    else:
                        for data in txt_data['isi']:
                            seq = float(data['po_no'])
                            po_line = self.env['purchase.order.line'].sudo().search([
                                ('sequence', '=', int(seq))], limit=1)
                            if po_line and data['poitem_del']=='L':
                                po_line.write({'active': False})

                    if vals:
                        po_create = self.env['purchase.order'].sudo().create({
                            'name': txt_data['po_doc'],
                            'payment_term_id':payment_term.id if payment_term else False,
                            'partner_id': vendor.id if vendor else False,
                            'project_id': profit_center,
                            'branch_id': branch_id,
                            'department_id': department_id,
                            'order_line': vals,
                            'price_cut_ids':potongan,
                            'currency_id': curr.id,
                            'begin_date': txt_data['po_dcdat'],
                            'po_type': txt_data['po_jenis'],
                            'state': state,
                            'tgl_create_sap': txt_data['po_crdat']

                        })
                        po_create.get_gr()
            self.status='OK'
        else:
            raise UserError(_("Data PO Tidak Tersedia!"))

    def assign_todo_first(self):
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'purchase.order')], limit=1)
        po = self.env['purchase.order'].search([('name', '=', self.name)], limit=1)

        for res in po:
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
                        'nomor_po': res.name,
                        'date_deadline': fields.Date.today() + timedelta(days=5),
                        'state': 'planned',
                        'summary': f"Need Upload Document {model_id.name}!"
                    })
            # Get Document Setting
            document_list = []
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])
            self.status="Assign"

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

class paymentall_ncl_class(models.TransientModel):
    """
    This wizard will confirm the all the selected no.swift
    """

    _name = "wika.get.po.all"
    _description = "Get PO Selected"

    def get_po_all(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['wika.get.po'].browse(active_ids):
            record.get_po()
        return {'type': 'ir.actions.act_window_close'}



    def asign_todo_all(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['wika.get.po'].browse(active_ids):
            record.assign_todo_first()
        return {'type': 'ir.actions.act_window_close'}
