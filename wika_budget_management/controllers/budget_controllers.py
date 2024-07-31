from odoo import http
from odoo.http import request, _logger, Response
import requests, json
from datetime import datetime

class BudgetController(http.Controller):
    
    @http.route('/create_budget', type='json', auth='public', methods=['POST'], csrf=False)
    def create_budget(self, **post):
        req_headers = request.httprequest.headers
        req_apikey =  req_headers['X-Api-Key']
        setting_apikey = request.env['res.company'].sudo().search([], limit=1).x_api_key
        if req_apikey == setting_apikey:
            req_data = request.get_json_data()
            if req_data:
                year = req_data['YEAR']
                profitcenter = req_data['PROFITCENTER']
                account = req_data['ACCOUNT']
                plan_amount = req_data['PLAN_AMOUNT']

                kode_perkiraan = request.env['account.account'].sudo().search([('company_id','=',1),('sap_code', '=', account)],limit=1)
                department = request.env['res.branch'].sudo().search([('sap_code', '=', profitcenter)],limit=1)

                if not kode_perkiraan:
                    Response.status_code = 200
                    return f"Kode Perkiraan: {account} tidak ditemukan di WDIGIFMS."
                if not department:
                    Response.status_code = 200
                    return f"Kode Profit Center: {profitcenter} tidak ditemukan di WDIGIFMS."
                
                property = request.env['ir.property'].sudo().search([
                    ('name','=','property_account_expense_categ_id'),
                    ('value_reference','ilike',str(kode_perkiraan.id))
                ], limit=1)

                if property:
                    product_id = request.env['product.product'].sudo().search([
                        # ('product_tmpl_id', '=', int(property.res_id[17:]))], limit=1)
                        ('product_tmpl_id', '=', int(property.res_id))], limit=1)
                    print(product_id)
                if not property:
                    Response.status_code = 200
                    return f"Product Budget: {account} tidak ditemukan di WDIGIFMS."
                
                if account[-0] == "7":
                    tipe_budget_id = request.env['wika.tipe.budget'].sudo().search([('code','=','opex')], limit=1)
                    tipe_budget = 'opex'
                else:
                    tipe_budget_id = request.env['wika.tipe.budget'].sudo().search([('code','=','capex')], limit=1)
                    tipe_budget = 'capex'
                
                if account[-0:4] == kode_perkiraan.sap_code[-0:4]:
                    grup_akun = request.env['wika.mcs.budget.parent'].sudo().search([
                        ('name', 'ilike', account[-0:4])
                    ], order='id desc', limit=1)

                if department.biro == True:
                    divisi = department.parent_id.id
                    dept = department.id
                    budget_exist = request.env['wika.mcs.budget.coa'].sudo().search([
                        ('kode_coa', '=', kode_perkiraan.id), ('department', '=', divisi),
                        ('biro', '=', dept), ('tahun', '=', year), ('from_sap', '=', True),
                        ('tipe_budget_id', '=', tipe_budget_id.id)], limit=1)
                else:
                    divisi = department.id
                    budget_exist = request.env['wika.mcs.budget.coa'].sudo().search([
                        ('kode_coa', '=', kode_perkiraan.id), ('department', '=', divisi),
                        ('tahun', '=', year),
                        ('from_sap', '=', True),
                        ('tipe_budget_id', '=', tipe_budget_id.id)], limit=1)

                if budget_exist:
                    budget_exist.write({'total_anggaran_sap': plan_amount})
                    result_done = {
                        "status": 200,
                        "message": 'Budget Updated',
                        "code": 200,
                    }
                    _logger.warning(result_done)
                    return result_done
                else:
                    try:
                        budget = request.env['wika.mcs.budget.coa'].sudo().create({
                            'tahun': year,
                            'department': divisi,
                            'biro': dept if department.biro == True else None,
                            'kode_coa': kode_perkiraan.id,
                            'tipe_budget_id': tipe_budget_id.id,
                            'tipe_budget':tipe_budget,
                            'aktif': 't',
                            'from_sap': True,
                            'state':'Draft',
                            'total_anggaran_sap': plan_amount,
                            'grup_akun': grup_akun.id or False,
                            'detail_ids': [(0, 0, {
                                'pekerjaan': product_id.id,
                                'vol': 1,
                                'harga_satuan': plan_amount,
                                'satuan':'Ls',
                                'total_anggaran': plan_amount
                            })],
                        })
                        budget.act_generate()
                        result_done = {
                            "status": 200,
                            "message": 'Budget Created',
                            "code": 200,
                        }
                        _logger.warning(result_done)
                        return result_done
                    except Exception as e:
                        result = {
                            "status": 400,
                            "message": 'Not Found' + str(e),
                        }
                        return result
            else:
                return Response("Can't fetch data", status=400)

        else:
            return Response("API Key is unmatched!", status=400)

    @http.route('/create_multi_budget', type='json', auth='public', methods=['POST'], csrf=False)
    def create_multi_budget(self, **post):
        req_headers = request.httprequest.headers
        req_apikey = req_headers.get('X-Api-Key')
        setting_apikey = request.env['res.company'].sudo().search([], limit=1).x_api_key

        if req_apikey == setting_apikey:
            req_data = request.get_json_data()
            if req_data:
                results = req_data.get('result', [])
                response = []

                for data in results:
                    year = data.get('YEAR')
                    profitcenter = data.get('PROFITCENTER')
                    account = data.get('ACCOUNT')
                    plan_amount = data.get('PLAN_AMOUNT')

                    kode_perkiraan = request.env['account.account'].sudo().search([
                        ('company_id', '=', 1),
                        ('sap_code', '=', account)
                    ], limit=1)
                    department = request.env['res.branch'].sudo().search([
                        ('sap_code', '=', profitcenter)
                    ], limit=1)

                    if not kode_perkiraan:
                        response.append({
                            "account": account,
                            "status": 200,
                            "message": "Kode Perkiraan: {} tidak ditemukan di WDIGIFMS.".format(account)
                        })
                        continue
                    if not department:
                        response.append({
                            "profitcenter": profitcenter,
                            "status": 200,
                            "message": "Kode Profit Center: {} tidak ditemukan di WDIGIFMS.".format(profitcenter)
                        })
                        continue
                    
                    property = request.env['ir.property'].sudo().search([
                        ('name', '=', 'property_account_expense_categ_id'),
                        ('value_reference', 'ilike', str(kode_perkiraan.id))
                    ], limit=1)

                    if property:
                        product_id = request.env['product.product'].sudo().search([
                            ('product_tmpl_id', '=', int(property.res_id))
                        ], limit=1)
                    if not property:
                        response.append({
                            "account": account,
                            "status": 200,
                            "message": "Product Budget: {} tidak ditemukan di WDIGIFMS.".format(account)
                        })
                        continue
                    
                    if account[-1] == "7":
                        tipe_budget_id = request.env['wika.tipe.budget'].sudo().search([('code', '=', 'opex')], limit=1)
                        tipe_budget = 'opex'
                    else:
                        tipe_budget_id = request.env['wika.tipe.budget'].sudo().search([('code', '=', 'capex')], limit=1)
                        tipe_budget = 'capex'
                    
                    if account[-4:] == kode_perkiraan.sap_code[-4:]:
                        grup_akun = request.env['wika.mcs.budget.parent'].sudo().search([
                            ('name', 'ilike', account[-4:])
                        ], order='id desc', limit=1)

                    if department.biro:
                        divisi = department.parent_id.id
                        dept = department.id
                        budget_exist = request.env['wika.mcs.budget.coa'].sudo().search([
                            ('kode_coa', '=', kode_perkiraan.id),
                            ('department', '=', divisi),
                            ('biro', '=', dept),
                            ('tahun', '=', year),
                            ('from_sap', '=', True),
                            ('tipe_budget_id', '=', tipe_budget_id.id)
                        ], limit=1)
                    else:
                        divisi = department.id
                        budget_exist = request.env['wika.mcs.budget.coa'].sudo().search([
                            ('kode_coa', '=', kode_perkiraan.id),
                            ('department', '=', divisi),
                            ('tahun', '=', year),
                            ('from_sap', '=', True),
                            ('tipe_budget_id', '=', tipe_budget_id.id)
                        ], limit=1)

                    if budget_exist:
                        budget_exist.write({'total_anggaran_sap': plan_amount})
                        response.append({
                            "account": account,
                            "status": 200,
                            "message": 'Budget Updated'
                        })
                    else:
                        try:
                            budget = request.env['wika.mcs.budget.coa'].sudo().create({
                                'tahun': year,
                                'department': divisi,
                                'biro': dept if department.biro else None,
                                'kode_coa': kode_perkiraan.id,
                                'tipe_budget_id': tipe_budget_id.id,
                                'tipe_budget': tipe_budget,
                                'aktif': 't',
                                'from_sap': True,
                                'state': 'Draft',
                                'total_anggaran_sap': plan_amount,
                                'grup_akun': grup_akun.id or False,
                                'detail_ids': [(0, 0, {
                                    'pekerjaan': product_id.id,
                                    'vol': 1,
                                    'harga_satuan': plan_amount,
                                    'satuan': 'Ls',
                                    'total_anggaran': plan_amount
                                })],
                            })
                            budget.act_generate()
                            response.append({
                                "account": account,
                                "status": 200,
                                "message": 'Budget Created'
                            })
                        except Exception as e:
                            response.append({
                                "account": account,
                                "status": 400,
                                "message": 'Not Found: ' + str(e),
                            })
                return Response(json.dumps(response), status=200, content_type='application/json')
            else:
                return Response("Can't fetch data", status=400)
        else:
            return Response("API Key is unmatched!", status=400)