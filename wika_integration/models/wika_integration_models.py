# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError, Warning
import logging, json
_logger = logging.getLogger(__name__)

class wika_integration(models.Model):
    _name = 'wika.integration'
    _description='Wika Integration'

    name = fields.Char(string="nama")
    app = fields.Selection(string="Application",
                           selection=[
                               ('PMCS', 'PMCS'),
                               ('SIMDIV', 'SIMDIV'),
                               ('SCM', 'SCM'),
                               ('SAP', 'SAP'),
                               ('CRM', 'CRM'),
                               ('WZONE', 'WZONE'),
                               ('HC', 'HC')])
    app_secret = fields.Char(string="Secret Key Application")
    url = fields.Char(string="URL")
    payload = fields.Text(string="Payload")
    _sql_constraints = [
        ('app_name_unique', 'unique (name)', 'Nama harus unik!')
    ]
    request_ids = fields.One2many(comodel_name='wika.integration.line',inverse_name='integration_id')
    api_user = fields.Char(string='API User')
    api_pword = fields.Char(string='API Password')

    def push_bap(self):
        api_config_sap_token = self.env['wika.integration'].sudo().search([('name', '=', 'URL_GET_TOKEN')], limit=1)
        api_config_sap_bap = self.env['wika.integration'].sudo().search([('name', '=', 'URL_SEND_BAP')], limit=1)
        headers_get = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json',
            'x-csrf-Token': 'fetch',
        }
        payload_get={}
        print ("lllllllllllllllllllllllllll")
        try:
            # 1. Get W-KEY TOKEN
            response = requests.request("GET", api_config_sap_token.url, data=payload_get, headers=headers_get)
            print(response)
            w_key = (response.headers['x-csrf-token'])
            csrf = str(w_key)
            headers_post= {
                'x-csrf-token': '6EDvH9D3XC5OhBVWeLKefw==',
                'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
                'Content-Type': 'application/json',
            }
            print (headers_post)
            payload_post =json.dumps({
                 "input":  [
                        {
                        "company_code" : "A000",
                        "document_no" : "5000000243",
                        "matdoc_year" : "2023",
                        "status":"X"
                        }
                    ]
                })
            #payload_post = payload_post.replace('\n', '')
            _logger.info(payload_post)
            response_2 = requests.request("POST", api_config_sap_bap.url, data=payload_post, headers=headers_post)
            print (response_2)
            txt = json.loads(response_2.text)
        except:
            raise UserError(_("Connection Failed. Please Check Your Internet Connection."))

        # auth_get_token = {
        #     'user': api_config_sap_token.api_user,
        #     'pword': api_config_sap_token.api_pword
        # }
        # auth_send_bap = {
        #     'user': api_config_sap_bap.api_user,
        #     'pword': api_config_sap_bap.api_pword
        # }
        #
        # is_sap_url = api_config_sap_token.url
        #
        # if auth_get_token['user'] == False or auth_get_token['pword'] == False:
        #     raise ValidationError(
        #         'User dan Password untuk membuat token API belum dikonfigurasi. Silakan hubungi Administrator terlebih dahulu.')
        # else:
        #     if auth_send_bap['user'] == False or auth_send_bap['pword'] == False:
        #         raise ValidationError(
        #             'User dan Password API untuk mengirim BAP ke SAP belum dikonfigurasi. Silakan hubungi Administrator terlebih dahulu.')
        #     else:
        #         headers = {'x-csrf-Token': 'fetch'}
        #         auth = (auth_get_token['user'], auth_get_token['pword'])
        #         response = requests.get(is_sap_url, headers=headers, auth=auth)
        #
        #         if response.status_code == 200 and "CSRF Token sent" in response.text:
        #             csrf_token = response.headers.get('x-csrf-token')
        #             auth_send = (auth_send_bap['user'], auth_send_bap['pword'])
        #
        #             payload = json.dumps({
        #                 "input": [
        #                     {
        #                         "company_code": "A000",
        #                         "document_no": "5000000243",
        #                         "matdoc_year": "2023"
        #                     }
        #                 ]
        #             })
        #
        #             headers_send = {
        #                 'x-csrf-token': csrf_token,
        #                 'Content-Type': 'application/json',
        #                 'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw=='
        #             }
        #
        #             print("HEADERSENDDD", headers_send)
        #             # tesssssdoeloeee
        #
        #             # response_post = requests.post(is_sap_url, headers=headers_send, json=payload)
        #             response_post = requests.request("POST", is_sap_url, headers=headers_send, data=payload,
        #                                              auth=auth_send)
        #
        #             print("POST Response Status Code:", response_post.status_code)
        #             print("POST Response Text:", response_post.text)
                    # tespost_tespost

class wika_integration_line(models.Model):
    _name = 'wika.integration.line'
    _description='Wika Integration.line'

    integration_id  = fields.Many2one(comodel_name='wika.integration')
    request= fields.Text(string='Request')
    request_date= fields.Datetime(string='Request Date')
    response = fields.Text(string='Response')