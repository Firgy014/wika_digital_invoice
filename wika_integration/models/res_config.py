from odoo import models, fields, api, exceptions, _
import requests
import json
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):

    _inherit= 'res.config.settings'


    # def get_po(self):
    #     url_config = self.env['wika.integration'].search([('name', '=', 'URL PO')], limit=1)
    #     url= url_config.url+'services/auth'
    #     url_get_po = url_config.url + 'services/getposap'
    #     print (url)
    #     headers = {
    #         'Content-Type': 'application/json'
    #     }
    #     payload = json.dumps({
    #         "entitas": "FMS",
    #         "skey": "OAZvRmB7HKDdDkKF29DXZwgSmlv9KqQWZNDWV51SACAbhnOvuA1AvZf5FnIBrLxC"
    #     })
    #     payload =payload.replace('\n', '')
    #     try:
    #         # 1. Get W-KEY TOKEN
    #         response = requests.request("POST", url, data=payload, headers=headers)
    #         w_key =(response.headers['w-key'])
    #         csrf = {'w-access-token': str(w_key)}
    #         headers.update(csrf)
    #         print (headers)
    #         response_2 = requests.request("POST", url_get_po, data=url_config.payload, headers=headers)
    #         txt = json.loads(response_2.text)
    #
    #     except:
    #         raise UserError(_("Connection Failed. Please Check Your Internet Connection."))
    #     if txt['data']:
    #         txt_data = txt['data']
    #         print (len(txt_data))
    #         # if len(txt_data)>4:
    #         #     for data in txt_data:
    #         #         vals = []
    #         #         isi = data['isi']
    #         #         for hasil in isi:
    #         #             print ("------------------------")
    #         #             if hasil['LOEKZ'] == 'L':
    #         #                 state = 'cancel'
    #         #             else:
    #         #                 state = 'po'
    #         #             print (type(hasil['BRTWR']))
    #         #             if data['jenis']=='JASA':
    #         #                 prod = self.env['product.product'].sudo().search([
    #         #                     ('default_code', '=', hasil['SRVPOS'])], limit=1)
    #         #                 price= float(hasil['BRTWR'])
    #         #                 qty=float(hasil['MENGE'])
    #         #                 price_unit= float(price/qty)*100
    #         #             else:
    #         #                 prod = self.env['product.product'].sudo().search([
    #         #                     ('default_code', '=', hasil['MATNR'])], limit=1)
    #         #                 qty = float(hasil['MENGE'])
    #         #                 price_unit= float(hasil['NETPR'])*100
    #         #             print (prod)
    #         #             if not prod:
    #         #                 return "Material/Service  : %s tidak ditemukan" % (hasil['SRVPOS'],hasil['MATNR'])
    #         #             tax= self.env['account.tax'].sudo().search([
    #         #                 ('name', '=', hasil['MWSKZ'])], limit=1)
    #         #             print(tax)
    #         #             if not tax:
    #         #                 return "Kode Pajak  : %s tidak ditemukan" % hasil['MWSKZ']
    #         #             curr=self.env['res.currency'].sudo().search([
    #         #                 ('name', '=', hasil['WAERS'])], limit=1)
    #         #             print(curr)
    #         #             if not curr:
    #         #                 continue
    #         #                 #return "Kode Currency  : %s tidak ditemukan" % hasil['WAERS']
    #         #             vendor = self.env['res.partner'].sudo().search([
    #         #                 ('sap_code', '=', hasil['LIFNR'])], limit=1)
    #         #             if not vendor:
    #         #                 print ("lllllllllllllllll")
    #         #                 continue
    #         #                 #return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
    #         #
    #         #             print ("vendor",vendor)
    #         #             uom= self.env['uom.uom'].sudo().search([
    #         #                 ('name', '=' ,hasil['MEINS'])] ,limit=1)
    #         #             if not uom:
    #         #                 uom = self.env['uom.uom'].sudo().create({
    #         #                     'name': hasil['MEINS'],'category_id':1})
    #         #             project  = self.env['project.project'].sudo().search([
    #         #                 ('sap_code', '=' ,data['PRCTR']), ('company_id', '=', 1)] ,limit=1)
    #         #             print (project)
    #         #             if project:
    #         #                 profit_center=project.id
    #         #                 branch_id = project.branch_id.id
    #         #                 department_id = None
    #         #             if not project:
    #         #                 branch = self.env['res.branch'].sudo().search([
    #         #                     ('sap_code', '=', data['PRCTR']), ('company_id', '=', 1)], limit=1)
    #         #                 if branch and branch.biro == True:
    #         #                     department_id= branch.id
    #         #                     branch_id=branch.parent_id.id
    #         #                     profit_center=None
    #         #                 if branch and branch.biro == False:
    #         #                     department_id = None
    #         #                     branch_id = branch.id
    #         #                     profit_center = None
    #         #                 if not branch:
    #         #                     return "Kode Profit Center : %s tidak ditemukan" % data['PRCTR']
    #         #             print (profit_center)
    #         #             vals.append((0,0, {
    #         #                 'sequence':int(hasil['EBELP']),
    #         #                 'product_id': prod.id if prod else False,
    #         #                 'product_qty':qty,
    #         #                 'product_uom':uom.id,
    #         #                 'price_unit':price_unit,
    #         #                 'taxes_id':[(6, 0, [x.id for x in tax])]
    #         #
    #         #             }))
    #         #             tgl_mulai=hasil['BEDAT_X']
    #         #             po_type = hasil['BSART']
    #         #             tgl_create_sap = hasil['AEDAT_X']
    #         #
    #         #             print (vals)
    #         #         if not vals:
    #         #             continue
    #         #         else:
    #         #             po_create= self.env['purchase.order'].sudo().create({
    #         #                 'name': data['EBELN'],
    #         #                 'partner_id': vendor.id if vendor else False,
    #         #                 'project_id':profit_center,
    #         #                 'branch_id':branch_id,
    #         #                 'department_id':department_id,
    #         #                 'order_line':vals,
    #         #                 'currency_id': curr.id,
    #         #                 'begin_date':tgl_mulai,
    #         #                 'po_type':data['jenis'],
    #         #                 'state':state,
    #         #                 'tgl_create_sap':tgl_create_sap
    #         #
    #         #             })
    #         # else:
    #         #
    #         #
    #         #     for data in txt_data['isi']:
    #         #         vals = []
    #         #
    #         #         print(data)
    #         #         if data['LOEKZ'] == 'L':
    #         #             state = 'cancel'
    #         #         else:
    #         #             state = 'po'
    #         #         print(state)
    #         #         # po_exist  = self.env['purchase.order'].sudo().search([
    #         #         #     ('name', '=' ,txt_data['EBELN']),('state','!=','cancel'),('tgl_create_sap','=',data['AEDAT_X'])] ,limit=1)
    #         #         # print("po_exist")
    #         #         # if po_exist:
    #         #         #     print ("masukkkkk")
    #         #         #     po_exist.write({'state': 'cancel'})
    #         #         #     break
    #         #         if txt_data['jenis'] == 'JASA':
    #         #             prod = self.env['product.product'].sudo().search([
    #         #                 ('default_code', '=', data['SRVPOS'])], limit=1)
    #         #             price = float(data['BRTWR'])
    #         #             qty = float(data['MENGE'])
    #         #             price_unit = float(price / qty) * 100
    #         #         else:
    #         #             prod = self.env['product.product'].sudo().search([
    #         #                 ('default_code', '=', data['MATNR'])], limit=1)
    #         #             qty = float(data['MENGE'])
    #         #             price_unit = float(data['NETPR']) * 100
    #         #         print(prod)
    #         #         if not prod:
    #         #             return "Material/Service  : %s tidak ditemukan" % (data['SRVPOS'], data['MATNR'])
    #         #         tax = self.env['account.tax'].sudo().search([
    #         #             ('name', '=', data['MWSKZ'])], limit=1)
    #         #         print(tax)
    #         #         if not tax:
    #         #             return "Kode Pajak  : %s tidak ditemukan" % data['MWSKZ']
    #         #         curr = self.env['res.currency'].sudo().search([
    #         #             ('name', '=', data['WAERS'])], limit=1)
    #         #         print(curr)
    #         #
    #         #         if not curr:
    #         #             break
    #         #             # return "Kode Currency  : %s tidak ditemukan" % hasil['WAERS']
    #         #         vendor = self.env['res.partner'].sudo().search([
    #         #             ('sap_code', '=', data['LIFNR'])], limit=1)
    #         #         if not vendor:
    #         #             print("lllllllllllllllll")
    #         #             return "Vendor  : %s tidak ditemukan" % data['LIFNR']
    #         #
    #         #         print("vendor", vendor)
    #         #         uom = self.env['uom.uom'].sudo().search([
    #         #             ('name', '=', data['MEINS'])], limit=1)
    #         #         if not uom:
    #         #             uom = self.env['uom.uom'].sudo().create({
    #         #                 'name': data['MEINS'], 'category_id': 1})
    #         #         project = self.env['project.project'].sudo().search([
    #         #             ('sap_code', '=', txt_data['PRCTR']), ('company_id', '=', 1)], limit=1)
    #         #         print(project)
    #         #         if project:
    #         #             profit_center = project.id
    #         #             branch_id = project.branch_id.id
    #         #             department_id = None
    #         #         if not project:
    #         #             branch = self.env['res.branch'].sudo().search([
    #         #                 ('sap_code', '=', txt_data['PRCTR']), ('company_id', '=', 1)], limit=1)
    #         #             if branch and branch.biro == True:
    #         #                 department_id = branch.id
    #         #                 branch_id = branch.parent_id.id
    #         #                 profit_center = None
    #         #             if branch and branch.biro == False:
    #         #                 department_id = None
    #         #                 branch_id = branch.id
    #         #                 profit_center = None
    #         #             if not branch:
    #         #                 return "Kode Profit Center : %s tidak ditemukan" % txt_data['PRCTR']
    #         #         vals.append((0, 0, {
    #         #             'sequence': int(data['EBELP']),
    #         #             'product_id': prod.id if prod else False,
    #         #             'product_qty': qty,
    #         #             'product_uom': uom.id,
    #         #             'price_unit': price_unit,
    #         #             'taxes_id': [(6, 0, [x.id for x in tax])]
    #         #
    #         #         }))
    #         #         tgl_mulai = data['BEDAT_X']
    #         #         po_type = data['BSART']
    #         #         tgl_create_sap = data['AEDAT_X']
    #         #
    #         #     po_create = self.env['purchase.order'].sudo().create({
    #         #         'name': txt_data['EBELN'],
    #         #         'partner_id': vendor.id if vendor else False,
    #         #         'project_id': profit_center,
    #         #         'branch_id': branch_id,
    #         #         'department_id': department_id,
    #         #         'order_line': vals,
    #         #         'currency_id': curr.id,
    #         #         'begin_date': tgl_mulai,
    #         #         'po_type': txt_data['jenis'],
    #         #         'state': state,
    #         #         'tgl_create_sap':tgl_create_sap
    #         #     })
    #         if len(txt_data) > 4:
    #             for data in txt_data:
    #                 vals = []
    #                 isi = data['isi']
    #                 for hasil in isi:
    #                     print("------------------------")
    #                     if hasil['LOEKZ'] == 'L':
    #                         continue
    #                         #state = 'cancel'
    #                     else:
    #                         state = 'po'
    #                     print(type(hasil['BRTWR']))
    #                     if data['jenis'] == 'JASA':
    #                         prod = self.env['product.product'].sudo().search([
    #                             ('default_code', '=', hasil['SRVPOS'])], limit=1)
    #                         price = float(hasil['BRTWR'])
    #                         qty = float(hasil['MENGE'])
    #                         price_unit = float(price / qty) * 100
    #                     else:
    #                         prod = self.env['product.product'].sudo().search([
    #                             ('default_code', '=', hasil['MATNR'])], limit=1)
    #                         qty = float(hasil['MENGE'])
    #                         price_unit = float(hasil['NETPR']) * 100
    #                     print(prod)
    #                     if not prod:
    #                         return "Material/Service  : %s tidak ditemukan" % (hasil['SRVPOS'], hasil['MATNR'])
    #                     tax = self.env['account.tax'].sudo().search([
    #                         ('name', '=', hasil['MWSKZ'])], limit=1)
    #                     print(tax)
    #                     if not tax:
    #                         return "Kode Pajak  : %s tidak ditemukan" % hasil['MWSKZ']
    #                     curr = self.env['res.currency'].sudo().search([
    #                         ('name', '=', hasil['WAERS'])], limit=1)
    #                     print(curr)
    #                     if not curr:
    #                         continue
    #                         # return "Kode Currency  : %s tidak ditemukan" % hasil['WAERS']
    #                     vendor = self.env['res.partner'].sudo().search([
    #                         ('sap_code', '=', hasil['LIFNR'])], limit=1)
    #                     if not vendor:
    #                         print("lllllllllllllllll")
    #                         continue
    #                         # return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
    #
    #                     print("vendor", vendor)
    #                     uom = self.env['uom.uom'].sudo().search([
    #                         ('name', '=', hasil['MEINS'])], limit=1)
    #                     if not uom:
    #                         uom = self.env['uom.uom'].sudo().create({
    #                             'name': hasil['MEINS'], 'category_id': 1})
    #                     project = self.env['project.project'].sudo().search([
    #                         ('sap_code', '=', data['PRCTR']), ('company_id', '=', 1)], limit=1)
    #                     print(project)
    #                     if project:
    #                         profit_center = project.id
    #                         branch_id = project.branch_id.id
    #                         department_id = None
    #                     if not project:
    #                         branch = self.env['res.branch'].sudo().search([
    #                             ('sap_code', '=', data['PRCTR']), ('company_id', '=', 1)], limit=1)
    #                         if branch and branch.biro == True:
    #                             department_id = branch.id
    #                             branch_id = branch.parent_id.id
    #                             profit_center = None
    #                         if branch and branch.biro == False:
    #                             department_id = None
    #                             branch_id = branch.id
    #                             profit_center = None
    #                         if not branch:
    #                             return "Kode Profit Center : %s tidak ditemukan" % data['PRCTR']
    #                     print(profit_center)
    #                     vals.append((0, 0, {
    #                         'sequence': int(hasil['EBELP']),
    #                         'product_id': prod.id if prod else False,
    #                         'product_qty': qty,
    #                         'product_uom': uom.id,
    #                         'price_unit': price_unit,
    #                         'taxes_id': [(6, 0, [x.id for x in tax])]
    #
    #                     }))
    #                     tgl_mulai = hasil['BEDAT_X']
    #                     po_type = hasil['BSART']
    #                     tgl_create_sap = hasil['AEDAT_X']
    #
    #                     print(vals)
    #                 if not vals:
    #                     continue
    #                 else:
    #                     po_create = self.env['purchase.order'].sudo().create({
    #                         'name': data['EBELN'],
    #                         'partner_id': vendor.id if vendor else False,
    #                         'project_id': profit_center,
    #                         'branch_id': branch_id,
    #                         'department_id': department_id,
    #                         'order_line': vals,
    #                         'currency_id': curr.id,
    #                         'begin_date': tgl_mulai,
    #                         'po_type': data['jenis'],
    #                         'state': state,
    #                         'tgl_create_sap': tgl_create_sap
    #
    #                     })
    #         else:
    #
    #             for data in txt_data['isi']:
    #                 vals = []
    #
    #                 print(data)
    #                 if data['LOEKZ'] == 'L':
    #                     continue
    #                     #state = 'cancel'
    #                 else:
    #                     state = 'po'
    #                 print(state)
    #                 # po_exist  = self.env['purchase.order'].sudo().search([
    #                 #     ('name', '=' ,txt_data['EBELN']),('state','!=','cancel'),('tgl_create_sap','=',data['AEDAT_X'])] ,limit=1)
    #                 # print("po_exist")
    #                 # if po_exist:
    #                 #     print ("masukkkkk")
    #                 #     po_exist.write({'state': 'cancel'})
    #                 #     break
    #                 if txt_data['jenis'] == 'JASA':
    #                     prod = self.env['product.product'].sudo().search([
    #                         ('default_code', '=', data['SRVPOS'])], limit=1)
    #                     price = float(data['BRTWR'])
    #                     qty = float(data['MENGE'])
    #                     price_unit = float(price / qty) * 100
    #                 else:
    #                     prod = self.env['product.product'].sudo().search([
    #                         ('default_code', '=', data['MATNR'])], limit=1)
    #                     qty = float(data['MENGE'])
    #                     price_unit = float(data['NETPR']) * 100
    #                 print(prod)
    #                 if not prod:
    #                     return "Material/Service  : %s tidak ditemukan" % (data['SRVPOS'], data['MATNR'])
    #                 tax = self.env['account.tax'].sudo().search([
    #                     ('name', '=', data['MWSKZ'])], limit=1)
    #                 print(tax)
    #                 if not tax:
    #                     return "Kode Pajak  : %s tidak ditemukan" % data['MWSKZ']
    #                 curr = self.env['res.currency'].sudo().search([
    #                     ('name', '=', data['WAERS'])], limit=1)
    #                 print(curr)
    #
    #
    #                 vendor = self.env['res.partner'].sudo().search([
    #                     ('sap_code', '=', data['LIFNR'])], limit=1)
    #                 if not vendor:
    #                     print("lllllllllllllllll")
    #                     return "Vendor  : %s tidak ditemukan" % data['LIFNR']
    #
    #                 print("vendor", vendor)
    #                 uom = self.env['uom.uom'].sudo().search([
    #                     ('name', '=', data['MEINS'])], limit=1)
    #                 if not uom:
    #                     uom = self.env['uom.uom'].sudo().create({
    #                         'name': data['MEINS'], 'category_id': 1})
    #                 project = self.env['project.project'].sudo().search([
    #                     ('sap_code', '=', txt_data['PRCTR']), ('company_id', '=', 1)], limit=1)
    #                 print(project)
    #                 if project:
    #                     profit_center = project.id
    #                     branch_id = project.branch_id.id
    #                     department_id = None
    #                 if not project:
    #                     branch = self.env['res.branch'].sudo().search([
    #                         ('sap_code', '=', txt_data['PRCTR']), ('company_id', '=', 1)], limit=1)
    #                     if branch and branch.biro == True:
    #                         department_id = branch.id
    #                         branch_id = branch.parent_id.id
    #                         profit_center = None
    #                     if branch and branch.biro == False:
    #                         department_id = None
    #                         branch_id = branch.id
    #                         profit_center = None
    #                     if not branch:
    #                         return "Kode Profit Center : %s tidak ditemukan" % txt_data['PRCTR']
    #                 vals.append((0, 0, {
    #                     'sequence': int(data['EBELP']),
    #                     'product_id': prod.id if prod else False,
    #                     'product_qty': qty,
    #                     'product_uom': uom.id,
    #                     'price_unit': price_unit,
    #                     'taxes_id': [(6, 0, [x.id for x in tax])]
    #
    #                 }))
    #                 print ("okeeeeeeeeeeeeeeeeeee")
    #                 tgl_mulai = data['BEDAT_X']
    #                 po_type = data['BSART']
    #                 tgl_create_sap = data['AEDAT_X']
    #             if vals:
    #                 po_create = self.env['purchase.order'].sudo().create({
    #                     'name': txt_data['EBELN'],
    #                     'partner_id': vendor.id if vendor else False,
    #                     'project_id': profit_center,
    #                     'branch_id': branch_id,
    #                     'department_id': department_id,
    #                     'order_line': vals,
    #                     'currency_id': curr.id,
    #                     'begin_date': tgl_mulai,
    #                     'po_type': txt_data['jenis'],
    #                     'state': state,
    #                     'tgl_create_sap': tgl_create_sap
    #                 })
    #
    #     else:
    #         raise UserError(_("Data PO Tidak Tersedia!"))

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
            response_2 = requests.request("POST", url_get_po, data=url_config.payload, headers=headers)
            txt = json.loads(response_2.text)
            log_request_api = self.env['wika.integration.line'].sudo().create({
                    'integration_id': url_config.id,
                    'request': url_config.payload,
                    'request_date': fields.Datetime.now(),
                    'response' :txt['data'],
                })

        except:
            raise UserError(_("Connection Failed. Please Check Your Internet Connection."))
        if txt['data']:
            txt_data = txt['data']
            print ((txt_data))
            #print (txt_data.index())
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
                        print (data['po_doc'])
                        po = self.env['purchase.order'].sudo().search([
                            ('name', '=', data['po_doc']), ('tgl_create_sap', '=', data['po_crdat']),
                            ('state', '!=', 'cancel')], limit=1)
                        if not po:
                            dp= float(data['dp_amt'])
                            retensi=float(data['ret_pc'])
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
                                if data['po_jenis'] == 'JASA':
                                    qty = float(hasil['po_qty'])
                                    price_x = float(hasil['po_price'])
                                    print (price_x/qty)
                                    print ("lllllllllllllllllllllllllllllllllllllllll")
                                    price = float(price_x/qty)*10
                                else:
                                    qty = float(hasil['po_qty'])
                                    price = float(hasil['po_price'])
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
                                    print("lllllllllllllllll")
                                    continue
                                    # return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
                                uom = self.env['uom.uom'].sudo().search([
                                    ('name', '=', hasil['po_uom'])], limit=1)
                                if not uom:
                                    uom = self.env['uom.uom'].sudo().create({
                                        'name': hasil['po_uom'], 'category_id': 1})
                                project = self.env['project.project'].sudo().search([
                                    ('sap_code', '=', data['prctr']), ('company_id', '=', 1)], limit=1)
                                print(project)
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
                            if txt_data['po_jenis'] == 'JASA':
                                qty = float(data['po_qty'])
                                price_x = float(data['po_price'])
                                print ("oooooooooooooooooooooooooooooooooooo")
                                price = float(price_x/qty)*10
                            else:
                                qty = float(data['po_qty'])
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
                                print("lllllllllllllllll")
                                continue
                                # return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
                            uom = self.env['uom.uom'].sudo().search([
                                ('name', '=', data['po_uom'])], limit=1)
                            if not uom:
                                uom = self.env['uom.uom'].sudo().create({
                                    'name': data['po_uom'], 'category_id': 1})
                            project = self.env['project.project'].sudo().search([
                                ('sap_code', '=', txt_data['prctr']), ('company_id', '=', 1)], limit=1)
                            print(project)
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
            print ("hanya 1")
            # if len(txt_data) > 4:
            #     for data in txt_data:
            #         vals = []
            #         isi = data['isi']
            #         for hasil in isi:
            #             print("------------------------")
            #             if hasil['LOEKZ'] == 'L':
            #                 continue
            #                 #state = 'cancel'
            #             else:
            #                 state = 'po'
            #             print(type(hasil['BRTWR']))
            #             if data['jenis'] == 'JASA':
            #                 prod = self.env['product.product'].sudo().search([
            #                     ('default_code', '=', hasil['SRVPOS'])], limit=1)
            #                 price = float(hasil['BRTWR'])
            #                 qty = float(hasil['MENGE'])
            #                 price_unit = float(price / qty) * 100
            #             else:
            #                 prod = self.env['product.product'].sudo().search([
            #                     ('default_code', '=', hasil['MATNR'])], limit=1)
            #                 qty = float(hasil['MENGE'])
            #                 price_unit = float(hasil['NETPR']) * 100
            #             print(prod)
            #             if not prod:
            #                 return "Material/Service  : %s tidak ditemukan" % (hasil['SRVPOS'], hasil['MATNR'])
            #             tax = self.env['account.tax'].sudo().search([
            #                 ('name', '=', hasil['MWSKZ'])], limit=1)
            #             print(tax)
            #             if not tax:
            #                 return "Kode Pajak  : %s tidak ditemukan" % hasil['MWSKZ']
            #             curr = self.env['res.currency'].sudo().search([
            #                 ('name', '=', hasil['WAERS'])], limit=1)
            #             print(curr)
            #             if not curr:
            #                 continue
            #                 # return "Kode Currency  : %s tidak ditemukan" % hasil['WAERS']
            #             vendor = self.env['res.partner'].sudo().search([
            #                 ('sap_code', '=', hasil['LIFNR'])], limit=1)
            #             if not vendor:
            #                 print("lllllllllllllllll")
            #                 continue
            #                 # return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
            #
            #             print("vendor", vendor)
            #             uom = self.env['uom.uom'].sudo().search([
            #                 ('name', '=', hasil['MEINS'])], limit=1)
            #             if not uom:
            #                 uom = self.env['uom.uom'].sudo().create({
            #                     'name': hasil['MEINS'], 'category_id': 1})
            #             project = self.env['project.project'].sudo().search([
            #                 ('sap_code', '=', data['PRCTR']), ('company_id', '=', 1)], limit=1)
            #             print(project)
            #             if project:
            #                 profit_center = project.id
            #                 branch_id = project.branch_id.id
            #                 department_id = None
            #             if not project:
            #                 branch = self.env['res.branch'].sudo().search([
            #                     ('sap_code', '=', data['PRCTR']), ('company_id', '=', 1)], limit=1)
            #                 if branch and branch.biro == True:
            #                     department_id = branch.id
            #                     branch_id = branch.parent_id.id
            #                     profit_center = None
            #                 if branch and branch.biro == False:
            #                     department_id = None
            #                     branch_id = branch.id
            #                     profit_center = None
            #                 if not branch:
            #                     return "Kode Profit Center : %s tidak ditemukan" % data['PRCTR']
            #             print(profit_center)
            #             vals.append((0, 0, {
            #                 'sequence': int(hasil['EBELP']),
            #                 'product_id': prod.id if prod else False,
            #                 'product_qty': qty,
            #                 'product_uom': uom.id,
            #                 'price_unit': price_unit,
            #                 'taxes_id': [(6, 0, [x.id for x in tax])]
            #
            #             }))
            #             tgl_mulai = hasil['BEDAT_X']
            #             po_type = hasil['BSART']
            #             tgl_create_sap = hasil['AEDAT_X']
            #
            #             print(vals)
            #         if not vals:
            #             continue
            #         else:
            #             po_create = self.env['purchase.order'].sudo().create({
            #                 'name': data['EBELN'],
            #                 'partner_id': vendor.id if vendor else False,
            #                 'project_id': profit_center,
            #                 'branch_id': branch_id,
            #                 'department_id': department_id,
            #                 'order_line': vals,
            #                 'currency_id': curr.id,
            #                 'begin_date': tgl_mulai,
            #                 'po_type': data['jenis'],
            #                 'state': state,
            #                 'tgl_create_sap': tgl_create_sap
            #
            #             })
            # else:
            #
            #     for data in txt_data['isi']:
            #         vals = []
            #
            #         print(data)
            #         if data['LOEKZ'] == 'L':
            #             continue
            #             #state = 'cancel'
            #         else:
            #             state = 'po'
            #         print(state)
            #         # po_exist  = self.env['purchase.order'].sudo().search([
            #         #     ('name', '=' ,txt_data['EBELN']),('state','!=','cancel'),('tgl_create_sap','=',data['AEDAT_X'])] ,limit=1)
            #         # print("po_exist")
            #         # if po_exist:
            #         #     print ("masukkkkk")
            #         #     po_exist.write({'state': 'cancel'})
            #         #     break
            #         if txt_data['jenis'] == 'JASA':
            #             prod = self.env['product.product'].sudo().search([
            #                 ('default_code', '=', data['SRVPOS'])], limit=1)
            #             price = float(data['BRTWR'])
            #             qty = float(data['MENGE'])
            #             price_unit = float(price / qty) * 100
            #         else:
            #             prod = self.env['product.product'].sudo().search([
            #                 ('default_code', '=', data['MATNR'])], limit=1)
            #             qty = float(data['MENGE'])
            #             price_unit = float(data['NETPR']) * 100
            #         print(prod)
            #         if not prod:
            #             return "Material/Service  : %s tidak ditemukan" % (data['SRVPOS'], data['MATNR'])
            #         tax = self.env['account.tax'].sudo().search([
            #             ('name', '=', data['MWSKZ'])], limit=1)
            #         print(tax)
            #         if not tax:
            #             return "Kode Pajak  : %s tidak ditemukan" % data['MWSKZ']
            #         curr = self.env['res.currency'].sudo().search([
            #             ('name', '=', data['WAERS'])], limit=1)
            #         print(curr)
            #
            #
            #         vendor = self.env['res.partner'].sudo().search([
            #             ('sap_code', '=', data['LIFNR'])], limit=1)
            #         if not vendor:
            #             print("lllllllllllllllll")
            #             return "Vendor  : %s tidak ditemukan" % data['LIFNR']
            #
            #         print("vendor", vendor)
            #         uom = self.env['uom.uom'].sudo().search([
            #             ('name', '=', data['MEINS'])], limit=1)
            #         if not uom:
            #             uom = self.env['uom.uom'].sudo().create({
            #                 'name': data['MEINS'], 'category_id': 1})
            #         project = self.env['project.project'].sudo().search([
            #             ('sap_code', '=', txt_data['PRCTR']), ('company_id', '=', 1)], limit=1)
            #         print(project)
            #         if project:
            #             profit_center = project.id
            #             branch_id = project.branch_id.id
            #             department_id = None
            #         if not project:
            #             branch = self.env['res.branch'].sudo().search([
            #                 ('sap_code', '=', txt_data['PRCTR']), ('company_id', '=', 1)], limit=1)
            #             if branch and branch.biro == True:
            #                 department_id = branch.id
            #                 branch_id = branch.parent_id.id
            #                 profit_center = None
            #             if branch and branch.biro == False:
            #                 department_id = None
            #                 branch_id = branch.id
            #                 profit_center = None
            #             if not branch:
            #                 return "Kode Profit Center : %s tidak ditemukan" % txt_data['PRCTR']
            #         vals.append((0, 0, {
            #             'sequence': int(data['EBELP']),
            #             'product_id': prod.id if prod else False,
            #             'product_qty': qty,
            #             'product_uom': uom.id,
            #             'price_unit': price_unit,
            #             'taxes_id': [(6, 0, [x.id for x in tax])]
            #
            #         }))
            #         print ("okeeeeeeeeeeeeeeeeeee")
            #         tgl_mulai = data['BEDAT_X']
            #         po_type = data['BSART']
            #         tgl_create_sap = data['AEDAT_X']
            #     if vals:
            #         po_create = self.env['purchase.order'].sudo().create({
            #             'name': txt_data['EBELN'],
            #             'partner_id': vendor.id if vendor else False,
            #             'project_id': profit_center,
            #             'branch_id': branch_id,
            #             'department_id': department_id,
            #             'order_line': vals,
            #             'currency_id': curr.id,
            #             'begin_date': tgl_mulai,
            #             'po_type': txt_data['jenis'],
            #             'state': state,
            #             'tgl_create_sap': tgl_create_sap
            #         })

        else:
            raise UserError(_("Data PO Tidak Tersedia!"))


    def get_gr(self):
        url_config = self.env['wika.integration'].search([('name', '=', 'URL GR')], limit=1).url

        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request("GET", url_config.url, data=url_config.payload, headers=headers)
            txt = json.loads(response.text)

        except:
            raise UserError(_("Connection Failed. Please Check Your Internet Connection."))
        if txt['DATA']:
            txt_data = txt['DATA']
            vals=[]
            vals_header=[]
            for hasil in txt_data:
                print (hasil)
                # po_exist  = self.env['purchase.order'].sudo().search([
                #     ('name', '=' ,hasil['PO_NUMBER'])] ,limit=1)
                # da
                # if po_exist:
                #     prod = self.env['product.product'].sudo().search([
                #         ('default_code', '=', hasil['MATERIAL'])], limit=1)
                #     qty = float(hasil['QUANTITY']) * 100
                #     uom = self.env['uom.uom'].sudo().search([
                #         ('name', '=', hasil['MEINS'])], limit=1)
                #     if not uom:
                #         uom = self.env['uom.uom'].sudo().create({
                #             'name': hasil['MEINS'], 'category_id': 1})
                #     vals.append((0, 0, {
                #         'product_id': prod.id if prod else False,
                #         'quantity_done': qty,
                #         'product_uom': uom.id,
                #     }))
                #     vals_header.append((0, 0, {
                #         'name': hasil['MAT_DOC'],
                #         'po_id': po_exist.id,
                #         'project_id': po_exist.project_id.id,
                #         'branch_id': po_exist.branch_id.id,
                #         'department_id': po_exist.department_id.id,
                #         'scheduled_date':hasil['DOC_DATE']
                #     }))
                #     move_create = self.env['stock.move'].sudo().create({
                #
                #
                #         'order_line': vals,
                #         'currency_id': curr.id,
                #         'begin_date': tgl_mulai,
                #         'po_type': po_type,
                #         'state': state,
                #     })
                # kode_coa_sap = hasil['SAKNR_SKAT']
                # kode_company = hasil['BUKRS']
                # nama_coa =hasil['TXT20']
                # coa_exist  = self.env['account.account'].sudo().search([
                #     ('code', '=' ,kode_coa_sap[:-3]), ('company_id', '=', 1)] ,limit=1)
                # if coa_exist:
                #     coa_exist.write({'sap_code': kode_coa_sap ,'name' :nama_coa})
                # else:
                #     account = self.env['account.account'].sudo().create({
                #         'code': kode_coa_sap[:-3],
                #         'name': nama_coa,
                #         'sap_code': kode_coa_sap,
                #         'company_id' :1,
                #         'user_type_id' :9
                #     })

        else:
            raise UserError(_("Data GR Tidak Tersedia!"))
