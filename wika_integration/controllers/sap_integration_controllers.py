from odoo import http
from odoo.http import request
import json
from . import helpers
import os

class SAPControllerUpdateInvoice(http.Controller):
    @http.route("/wdigi/fetch-token", type='http', auth="none", csrf=False)
    def fetch_token(self):
        req_headers = request.get_http_params()
        wdigi_token = req_headers['wdigi-token']
        
        if wdigi_token == 'fetch':
            token = helpers._get_wdigi_token()
            if token:
                request.session['auth_token'] = token
                return json.dumps({'result': 200, 'wdigi-token': token})
                
    # API using JSON
    # @http.route("/wdigi/update-invoice", type='json', auth="none", csrf=False)
    # def update_invoice(self):
    #     invoice_model = request.env['account.move'].sudo()

    #     req_headers = request.httprequest.headers

    #     if req_headers['WDigi-Auth-Token'] != '':
    #         if request.session.get('auth_token') == req_headers['WDigi-Auth-Token']:
    #             req_data = request.get_json_data()
    #             invoices_data = req_data.get('result', [])
    #             updated_invoices = []
    #             for invoice_data in invoices_data:
    #                 no_inv = invoice_data['NO_INV']
    #                 invoice_id = invoice_model.search([('name', '=', no_inv)], limit=1)
    #                 if invoice_id:
    #                     invoice_id.write({
    #                         'invoice_number': no_inv,
    #                         'year': invoice_data['YEAR'],
    #                         'payment_reference': invoice_data['ACC_DOC'],
    #                     })
    #                     updated_invoices.append(no_inv)
    #                 else:
    #                     return json.dumps({
    #                         'result': 500,
    #                         'error': f'Invoice {no_inv} not found'
    #                     })
    #             if updated_invoices:
    #                 return json.dumps({
    #                     'result': 200,
    #                     'message': f"Invoices {', '.join(updated_invoices)} have been updated"
    #                 })
    #             else:
    #                 return json.dumps({
    #                     'result': 500,
    #                     'error': 'No invoices were updated'
    #                 })
    #         else:
    #             return json.dumps({
    #                 'result': 500,
    #                 'error': 'Invalid or missing authentication token'
    #             })
    #     else:
    #         return json.dumps({
    #             'result': 500,
    #             'error': 'WDigi-Auth-Token header is missing'
    #         })

    # API using TXT
    @http.route("/wdigi/update-invoice", type='http', auth="none", csrf=False)
    def update_invoice(self):
        invoice_model = request.env['account.move'].sudo()
        conf_model = request.env['sap.integration.configure'].sudo()

        conf_id = conf_model.search([('sftp_folder_archive', '!=', False)], limit=1)
        if conf_id:
            outbound_dir = conf_id.sftp_folder_archive
            file_name_prefix = 'YFII015'
            for file_name in os.listdir(outbound_dir):
                if file_name.startswith(file_name_prefix):
                    file_path = os.path.join(outbound_dir, file_name)

        updated_invoices = []
        try:
            with open(file_path, 'r') as file:
                next(file)  # Skip the header line
                next(file)  # Skip the column titles
                for line in file:
                    invoice_data = line.strip().split('|')
                    no_inv = invoice_data[0]
                    invoice_id = invoice_model.search([('name', '=', no_inv)], limit=1)
                    if invoice_id:
                        invoice_id.write({
                            'invoice_number': invoice_data[1],
                            'year': invoice_data[2],
                            'payment_reference': invoice_data[3],
                            'dp_doc': invoice_data[4]
                        })
                        updated_invoices.append(no_inv)
                    else:
                        return json.dumps({
                            'result': 500,
                            'error': f'Invoice {no_inv} not found'
                        })
                    
        except FileNotFoundError:
            return json.dumps({
                'result': 500,
                'error': 'Invoice file not found'
            })

        if updated_invoices:
            return json.dumps({
                'result': 200,
                'message': f"Invoices {', '.join(updated_invoices)} have been updated"
            })
        else:
            return json.dumps({
                'result': 500,
                'error': 'No invoices were updated'
            })