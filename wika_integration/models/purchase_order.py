from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError
import requests
import logging, json
_logger = logging.getLogger(__name__)

class Purchase_Order(models.Model):
    _inherit='purchase.order'


    def update_po(self):
        url_config = self.env['wika.integration'].search([('name', '=', 'URL PO')], limit=1)
        url = url_config.url + 'services/auth'
        url_get_po = url_config.url + 'services/getposap'
        # print (url)
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "entitas": "FMS",
            "skey": "OAZvRmB7HKDdDkKF29DXZwgSmlv9KqQWZNDWV51SACAbhnOvuA1AvZf5FnIBrLxC"
        })
        payload = payload.replace('\n', '')
        try:
            # 1. Get W-KEY TOKEN
            response = requests.request("POST", url, data=payload, headers=headers)
            w_key = (response.headers['w-key'])
            csrf = {'w-access-token': str(w_key)}
            headers.update(csrf)
            if self.level=='Proyek':
                profit_center=self.project_id.sap_code
            else:
                profit_center=self.branch_id.sap_code
            payload_2 = json.dumps({"profit_center": "%s",
                                    "po_doc": "%s",
                                    "po_jenis": "",
                                    "po_dcdat": "",
                                    "po_crdat": "%s",
                                    "po_plant": "A000",
                                    "co_code": "A000",
                                    "po_del": "",
                                    "poitem_del": "",
                                    "incmp_cat": ""
                                    }) % (profit_center, self.name,self.tgl_create_sap)
            payload_2 = payload_2.replace('\n', '')
            _logger.info(payload_2)
            response_2 = requests.request("POST", url_get_po, data=payload_2, headers=headers)
            txt = json.loads(response_2.text)
            print (txt)
            if 'data' in txt:
                if txt['data']:
                    txt_data = txt['data']
                    for data in txt_data['isi']:
                        seq = float(data['po_no'])
                        po_line = self.env['purchase.order.line'].sudo().search([
                            ('order_id', '=', self.id),
                            ('sequence', '=', int(seq))], limit=1)
                        if po_line:
                            qty = float(data['po_qty'])
                            if data['poitem_del'] == 'L':
                                po_line.write({'active': False})
                            else:
                                if qty != po_line.quantity:
                                    po_line.write({'quantity': qty})
                            self.write({'notes': 'OK'})
                    else:
                        pass
            else:
                pass
        except:
            pass
            self.write({'notes': "tidak ada data update "})

            #raise UserError(_("Connection Failed. Please Check Your Internet Connection."))

    def update_gr(self):
        config = self.env['wika.integration'].search([('name', '=', 'URL GR')], limit=1)
        url_config = config.url
        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "IV_EBELN": "%s",
            "IV_REVERSE": "",
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
        self.env['wika.integration.line'].sudo().create({
            'integration_id': config.id,
            'request_date': fields.Date.today()})
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
                    vals = []
                    for item in items:
                        picking = self.env['stock.picking'].sudo().search([
                            ('name', '=', mat_doc)], limit=1)
                        if picking:
                            qty = float(item['QUANTITY']) * 100
                            move= self.env['stock.move'].sudo().search([
                            ('sequence', '=', item['MATDOC_ITM'])], limit=1)
                            if move and item['REVERSE']=='X':
                                move.write({'active':False})
                            if move and qty != move.product_uom_qty:
                                move.write({'product_uom_qty': qty,'quantity_done':qty})
                                picking.write({'note':'updated'})
                        else:
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
                            docdate = hasil['DOC_DATE']
                        if vals:
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
                    pass
                              #raise UserError(_("Data GR Tidak Tersedia di PO TERSEBUT!"))
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
                        picking = self.env['stock.picking'].sudo().search([
                            ('name', '=', ses_number)], limit=1)
                        if picking:
                            qty = float(item['QUANTITY']) * 100
                            move = self.env['stock.move'].sudo().search([
                                ('sequence', '=', item['MATDOC_ITM'])], limit=1)
                            if move and item['REVERSE'] == 'X':
                                move.write({'active': False})
                            if move and qty != move.product_uom_qty:
                                move.write({'product_uom_qty': qty, 'quantity_done': qty})
                                picking.write({'note': 'updated'})
                        else:
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
                            docdate = hasil['DOC_DATE']
                            matdoc = item['MAT_DOC']
                        if vals:
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
                        pass
                        #raise UserError(_("Data GR Tidak Tersedia di PO TERSEBUT!"))

            else:
                raise UserError(_("Data GR Tidak Tersedia!"))
