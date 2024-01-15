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
            print (txt_data)
            for hasil in txt_data:
                print (hasil)
                # project  = self.env['project.project'].sudo().search([
                #     ('sap_code', '=' ,hasil['PRCTR']), ('company_id', '=', 1)] ,limit=1)
                # if project:
                #     profit_center=project.id
                #     branch_id = project.branch_id.id
                #     department_id = None
                # if not project:
                #     branch = self.env['res.branch'].sudo().search([
                #         ('sap_code', '=', hasil['PRCTR']), ('company_id', '=', 1)], limit=1)
                #     if branch and branch.biro == True:
                #         department_id= branch.id
                #         branch_id=branch.parent_id.id
                #     if branch and branch.biro == False:
                #         department_id = None
                #         branch_id = branch.id
                #     if not branch:
                #         return "Kode Profit Center : %s tidak ditemukan" % hasil['PRCTR']
                #
                # po_create= self.env['purchase.order'].sudo().create({
                #     'name': hasil['EBELN'],
                #
                # })
        #         # else:
        #         #     account = self.env['account.account'].sudo().create({
        #         #         'code': kode_coa_sap[:-3],
        #         #         'name': nama_coa,
        #         #         'sap_code': kode_coa_sap,
        #         #         'company_id' :1,
        #         #         'user_type_id' :9
        #         #     })
        #
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
