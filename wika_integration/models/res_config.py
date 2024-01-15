from odoo import models, fields, api, exceptions, _
import requests
import json
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):

    _inherit= 'res.config.settings'


    def get_po(self):
        url_config = self.env['wika.integration'].search([('name', '=', 'URL PO')], limit=1)
        url= url_config.url+'services/auth'
        url_get_po = url_config.url + 'services/getposap'
        print (url)
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
            print (headers)
            response_2 = requests.request("POST", url_get_po, data=url_config.payload, headers=headers)
            txt = json.loads(response_2.text)

        except:
            raise UserError(_("Connection Failed. Please Check Your Internet Connection."))
        if txt['data']:
            txt_data = txt['data']

            for data in txt_data:
                vals = []
                print (data)
                isi = data['isi']
                for hasil in isi:
                    if data['jenis']=='JASA':
                        prod = self.env['product.product'].sudo().search([
                            ('default_code', '=', hasil['SRVPOS'])], limit=1)
                        price= float(hasil['BRTWR'])
                        qty=float(hasil['MENGE'])
                        price_unit= float(price/qty)
                    else:
                        prod = self.env['product.product'].sudo().search([
                            ('default_code', '=', hasil['MATNR'])], limit=1)
                        price = float(hasil['NETPR'])
                        qty = float(hasil['MENGE'])
                        price_unit= float(price/qty)
                    if not prod:
                        return "Material/Service  : %s tidak ditemukan" % (hasil['SRVPOS'],hasil['MATNR'])
                    tax= self.env['account.tax'].sudo().search([
                        ('name', '=', hasil['MWSKZ'])], limit=1)
                    if not tax:
                        return "Kode Pajak  : %s tidak ditemukan" % hasil['MWSKZ']
                    curr=self.env['account.currency'].sudo().search([
                        ('name', '=', hasil['WAERS'])], limit=1)
                    if not curr:
                        return "Kode Currency  : %s tidak ditemukan" % hasil['WAERS']
                    vendor = self.env['res.partner'].sudo().search([
                        ('sap_code', '=', hasil['LIFNR'])], limit=1)
                    if not vendor:
                        return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']

                    print ("vendor",vendor)
                    uom= self.env['uom.uom'].sudo().search([
                        ('name', '=' ,hasil['MEINS'])] ,limit=1)
                    if not uom:
                        uom = self.env['uom.uom'].sudo().create({
                            'name': hasil['MEINS'],'category_id':1})
                    project  = self.env['project.project'].sudo().search([
                        ('sap_code', '=' ,data['PRCTR']), ('company_id', '=', 1)] ,limit=1)
                    if project:
                        profit_center=project.id
                        branch_id = project.branch_id.id
                        department_id = None
                    if not project:
                        branch = self.env['res.branch'].sudo().search([
                            ('sap_code', '=', data['PRCTR']), ('company_id', '=', 1)], limit=1)
                        if branch and branch.biro == True:
                            department_id= branch.id
                            branch_id=branch.parent_id.id
                            profit_center=None
                        if branch and branch.biro == False:
                            department_id = None
                            branch_id = branch.id
                            profit_center = None
                        if not branch:
                            return "Kode Profit Center : %s tidak ditemukan" % data['PRCTR']
                    vals.append((0,0, {
                        'product_id': prod.id if prod else False,
                        'product_qty':qty,
                        'product_uom':uom.id,
                        'price_unit':price_unit,
                        'taxes_id':[(6, 0, [x.id for x in tax])]

                    }))
                po_create= self.env['purchase.order'].sudo().create({
                    'name': data['EBELN'],
                    'partner_id': vendor.id if vendor else False,
                    'project_id':profit_center,
                    'branch_id':branch_id,
                    'department_id':department_id,
                    'order_line':vals,
                    'currency_id': curr.id,
                    'begin_date':data['BEDAT_X'],
                    'vendor_ref':data['IDNLF'],
                    'po_type':data['BSART'],
                    'state':'po'
                })

        else:
            raise UserError(_("Data PO Tidak Tersedia!"))

    def get_gr(self):
        url = self.env['wika.integration'].search([('name', '=', 'URL GR')], limit=1).url

        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
                "IV_EBELN": "",
                "IW_CPUDT_RANGE": {
                    "CPUDT_LOW": "2023-03-17",
                    "CPUTM_LOW": "00:00:00",
                    "CPUDT_HIGH": "2023-03-17",
                    "CPUTM_HIGH": "23:59:59"
                }
            })
        payload =payload.replace('\n', '')
        try:
            response = requests.request("GET", url, data=payload, headers=headers)
            txt = json.loads(response.text)

        except:
            raise UserError(_("Connection Failed. Please Check Your Internet Connection."))
        if txt['DATA']:
            txt_data = txt['DATA']
            for hasil in txt_data:
                print (hasil)
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
