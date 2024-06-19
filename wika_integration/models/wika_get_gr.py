# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError, Warning
import logging, json
_logger = logging.getLogger(__name__)

class wika_get_po(models.Model):
    _name = 'wika.get.gr'
    _description='Wika Get GR'

    name = fields.Char(string="Nomor PO")
    tgl_mulai = fields.Date(string="Tgl Mulai")
    tgl_akhir = fields.Date(string="Tgl Akhir")
    status=fields.Char(string='Status')

    def get_gr(self):
        url_config = self.env['wika.integration'].search([('name', '=', 'URL GR')], limit=1).url
        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "IV_EBELN": "%s",
            "IV_REVERSE": "O",
            "IW_CPUDT_RANGE": {
                "CPUDT_LOW": "%s",
                "CPUTM_LOW": "00:00:00",
                "CPUDT_HIGH": "%s",
                "CPUTM_HIGH": "23:59:59"
            }
        }) % (self.name, self.tgl_mulai, self.tgl_akhir)
        payload = payload.replace('\n', '')
        print(payload)
        try:
            response = requests.request("GET", url_config, data=payload, headers=headers)
            txt = json.loads(response.text)

            #raise UserError(_("Connection Failed. Please Check Your Internet Connection."))
            po = self.env['purchase.order'].sudo().search([
                ('name', '=', self.name)], limit=1)
            if po.po_type != 'JASA':
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
                                     ('order_id', '=' ,po.id),('sequence','=',item['PO_ITEM'])] ,limit=1)
                            vals.append((0, 0, {
                                'sequence':item['MATDOC_ITM'],
                                'product_id': prod.id if prod else False,
                                'quantity_done': float(item['QUANTITY']),
                                'product_uom_qty': float(item['QUANTITY']),
                                'product_uom': uom.id,
                                #'active':active,
                                'wika_state':'waits',
                                'location_id': 4,
                                'location_dest_id': 8,
                                'purchase_line_id':po_line.id,
                                'name': hasil['PO_NUMBER']
                            }))
                            docdate = hasil['DOC_DATE']
                        if vals:
                            picking_create = self.env['stock.picking'].sudo().create({
                                'name': mat_doc,
                                'po_id': po.id,
                                'purchase_id':po.id,
                                'project_id': po.project_id.id,
                                'branch_id': po.branch_id.id,
                                'department_id': po.department_id.id if po.department_id.id else False,
                                'scheduled_date': docdate,
                                'start_date': docdate,
                                'partner_id': po.partner_id.id,
                                'location_id': 4,
                                'location_dest_id': 8,
                                'picking_type_id': 1,
                                'move_ids': vals,
                                'pick_type': 'gr',
                                #'move_ids_without_package':vals,
                                'company_id': 1,
                                'wika_state': 'waits'
                            })
                            self.status = 'OK'
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
                        vals = []
                        for item in items:
                            po = self.env['purchase.order'].sudo().search([
                                ('name', '=', self.name)], limit=1)
                            prod = self.env['product.product'].sudo().search([
                                ('default_code', '=', item['MATERIAL'])], limit=1)
                            qty = float(item['QUANTITY']) * 100
                            uom = self.env['uom.uom'].sudo().search([
                                ('name', '=', item['ENTRY_UOM'])], limit=1)
                            if not uom:
                                uom = self.env['uom.uom'].sudo().create({
                                    'name': hasil['ENTRY_UOM'], 'category_id': 1})
                            po_line = self.env['purchase.order.line'].sudo().search([
                                ('order_id', '=', po.id), ('sequence', '=', item['PO_ITEM'])], limit=1)
                            vals.append((0, 0, {
                                'sequence': item['MATDOC_ITM'],
                                'product_id': prod.id if prod else False,
                                'quantity_done': float(item['QUANTITY']),
                                'product_uom_qty': float(item['QUANTITY']),
                                'product_uom': uom.id,
                                #'active': active,
                                'wika_state':'waits',
                                'location_id': 4,
                                'location_dest_id': 8,
                                'purchase_line_id': po_line.id,
                                'name': hasil['PO_NUMBER']
                            }))
                            docdate = hasil['DOC_DATE']
                            matdoc = item['MAT_DOC']
                        if vals:
                            picking_create = self.env['stock.picking'].sudo().create({
                                'name': ses_number,
                                'po_id': po.id,
                                'purchase_id': po.id,
                                'project_id': po.project_id.id,
                                'branch_id': po.branch_id.id,
                                'department_id': po.department_id.id if po.department_id.id else False,
                                'scheduled_date': docdate,
                                'start_date': docdate,
                                'partner_id': po.partner_id.id,
                                'location_id': 4,
                                'location_dest_id': 8,
                                'picking_type_id': 1,
                                'move_ids': vals,
                                'pick_type': 'ses',
                                'origin':matdoc,
                                #'move_ids_without_package':vals,
                                'company_id': 1,
                                'wika_state': 'waits'
                            })
                            self.status = 'OK'
                        else:
                            raise UserError(_("Data GR Tidak Tersedia di PO TERSEBUT!"))

                else:
                    raise UserError(_("Data GR Tidak Tersedia!"))
        except:
            self.status='-'

    # def assign_todo_first(self):
    #     model_model = self.env['ir.model'].sudo()
    #     document_setting_model = self.env['wika.document.setting'].sudo()
    #     model_id = model_model.search([('model', '=', 'stock.picking')], limit=1)
    #     po = self.env['purchase.order'].search([('name', '=', self.name)], limit=1)
    #
    #     for res in self:
    #         level=res.level
    #         first_user = False
    #         if level:
    #             approval_id = self.env['wika.approval.setting'].sudo().search(
    #                 [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',res.pick_type)], limit=1)
    #             print('approval_idapproval_idapproval_id')
    #             approval_line_id = self.env['wika.approval.setting.line'].search([
    #                 ('sequence', '=', 1),
    #                 ('approval_id', '=', approval_id.id)
    #             ], limit=1)
    #             print(approval_line_id)
    #             groups_id = approval_line_id.groups_id
    #             if groups_id:
    #                 for x in groups_id.users:
    #                     if level == 'Proyek' and x.project_id == res.project_id:
    #                         first_user = x.id
    #                     if level == 'Divisi Operasi' and x.branch_id == res.branch_id:
    #                         first_user = x.id
    #                     if level == 'Divisi Fungsi' and x.department_id == res.department_id:
    #                         first_user = x.id
    #             print(first_user)
    #             #     # Createtodoactivity
    #             if first_user:
    #                 self.env['mail.activity'].sudo().create({
    #                     'activity_type_id': 4,
    #                     'res_model_id': model_id.id,
    #                     'res_id': res.id,
    #                     'user_id': first_user,
    #                     'nomor_po': res.po_id.name,
    #                     'date_deadline': fields.Date.today() + timedelta(days=2),
    #                     'state': 'planned',
    #                     'summary': f"Need Upload Document  {model_id.name}"
    #                 })
    #
    #         # Get Document Setting
    #         document_list = []
    #         doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id),('transaction_type', '=', self.pick_type)])
    #
    #         if doc_setting_id:
    #             for document_line in doc_setting_id:
    #                 document_list.append((0, 0, {
    #                     'picking_id': res.id,
    #                     'document_id': document_line.id,
    #                     'state': 'waiting'
    #                 }))
    #             res.document_ids = document_list
    #         else:
    #             raise AccessError("Either approval and/or document settings are not found. Please configure it first in the settings menu.")

class get_gr_all(models.TransientModel):
    """
    This wizard will confirm the all the selected no.swift
    """

    _name = "wika.get.gr.all"
    _description = "Get GR Selected"

    def get_gr_all(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['wika.get.gr'].browse(active_ids):
            record.get_gr()
        return {'type': 'ir.actions.act_window_close'}



