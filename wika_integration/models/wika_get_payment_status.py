# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning,AccessError
import logging, json
_logger = logging.getLogger(__name__)

class wika_get_payment_status(models.Model):
    _name = 'wika.get.payment.status'
    _description='Wika Get Payment Status'

    name = fields.Char(string="Nama", required=True)
    tgl_mulai = fields.Date(string="Tgl Mulai")
    tgl_akhir = fields.Date(string="Tgl Akhir")
    state = fields.Selection([
        ('not_done', 'Not Done'),
        ('done', 'Done')
    ], string='State')

    def get_payment_status(self):
        ''' This method is called from a cron job.
        '''
        _logger.info("# === get_payment_status === #")
        for rec in self:
            tgl_mulai = ''
            tgl_akhir = ''
            doc_number = ''
            if rec.state != 'done':
                if rec.tgl_mulai:
                    tgl_mulai = str(rec.tgl_mulai)
                if rec.tgl_akhir:
                    tgl_akhir = str(rec.tgl_akhir)
                doc_number = rec.name

                url_config = self.env['wika.integration'].search([('name', '=', 'URL_PAYMENT_STATUS')], limit=1).url
                headers = {
                    'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
                    'Content-Type': 'application/json'
                }

                payload = json.dumps({
                    "COMPANY_CODE": "A000",
                    "CLEAR_DATE": 
                        {   
                            "LOW": "%s",
                            "HIGH":"%s"
                        },
                    "DOC_NUMBER": "%s"
                }) % (tgl_mulai, tgl_akhir, doc_number)
                payload = payload.replace('\n', '')
                _logger.info("# === CEK PAYLOAD === #")
                _logger.info(payload)

                try:
                    response = requests.request("GET", url_config, data=payload, headers=headers)
                    txt = json.loads(response.text)

                    if txt['DATA']:
                        _logger.info("# === IMPORT DATA === #")
                        company_id = self.env.company.id
                        # _logger.info(txt['DATA'])
                        txt_data0 = sorted(txt['DATA'], key=lambda x: x["DOC_NUMBER"])
                        txt_data = filter(lambda x: (x["STATUS"] == "X"), txt_data0)
                        
                        # txt_data = txt['DATA']
                        for data in txt_data:
                            # _logger.info(data)
                            doc_number = data["DOC_NUMBER"]
                            year = str(data["YEAR"])
                            line_item = data["LINE_ITEM"]
                            amount = data["AMOUNT"]
                            clear_date = data["CLEAR_DATE"]
                            clear_doc = data["CLEAR_DOC"]
                            status = data["STATUS"]
                            new_name = doc_number+str(year)

                            date_format = '%Y-%m-%d'
                            date_from = datetime.strptime(year + '-01-01', date_format)
                            date_to = datetime.strptime(year + '-12-31', date_format)

                            _logger.info("# === CEK ACCOUNT MOVE === #" + year + doc_number )
                            account_move = False
                            account_move1 = self.env['account.move'].search([
                                ('move_type', '=', 'in_invoice'),
                                ('payment_reference', '=', doc_number),
                                ('year', '=', year)], limit=1)
                            if not account_move1:
                                account_move2 = self.env['account.move'].search([
                                    ('move_type', '=', 'in_invoice'),
                                    ('payment_reference', '=', doc_number),
                                    ('date', '>=', date_from), ('date', '<=', date_to)], limit=1)
                                _logger.info("# === ACCOUNT MOVE 2 === #")
                                if account_move2:
                                    account_move = account_move2
                            else:
                                account_move = account_move1
                                
                            _logger.info(account_move)
                            if account_move and account_move.partner_id.company_id.id:
                                account_move.write({
                                    'sap_amount_payment': abs(amount)
                                })
                                account_move._compute_status_payment()

                            else:
                                _logger.info("# === CEK PARTIAL PAYMENT REQUEST === #" + year + doc_number )
                                partial_payment_request = self.env['wika.partial.payment.request'].search([
                                    ('reference', '=', doc_number),
                                    ('year', '=', year)], limit=1)
                                if partial_payment_request and partial_payment_request.partner_id.company_id.id:
                                    sap_amount_payment = partial_payment_request.invoice_id.sap_amount_payment
                                    partial_payment_request.invoice_id.write({
                                        'sap_amount_payment': sap_amount_payment+abs(amount)
                                    })                                
                                    partial_payment_request.invoice_id._compute_status_payment()                                
                                    partial_payment_request.write({
                                        'payment_state': 'paid',
                                        'no_doc_sap': clear_doc
                                    })
                                            
                        rec.state = 'done'
                        _logger.info("# === IMPORT DATA SUKSES === #")
                    else:
                        raise UserError(_("Data Payment Status Tidak Tersedia!"))
                    
                except:
                    # _logger.info("ERRORRRRRRR")
                    # _logger.info(UserError)
                    rec.state = 'not_done'
                    pass

    def _auto_get_payment_status(self):
        ''' This method is called from a cron job.
        '''
        _logger.info("# === _auto_get_payment_status === #")
        records = self.search([])
        for rec in records:
            tgl_mulai = ''
            tgl_akhir = ''
            doc_number = ''
            if rec.state != 'done':
                if rec.tgl_mulai:
                    tgl_mulai = str(rec.tgl_mulai)
                if rec.tgl_akhir:
                    tgl_akhir = str(rec.tgl_akhir)
                doc_number = rec.name

                url_config = self.env['wika.integration'].search([('name', '=', 'URL_PAYMENT_STATUS')], limit=1).url
                headers = {
                    'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
                    'Content-Type': 'application/json'
                }

                payload = json.dumps({
                    "COMPANY_CODE": "A000",
                    "CLEAR_DATE": 
                        {   
                            "LOW": "%s",
                            "HIGH":"%s"
                        },
                    "DOC_NUMBER": "%s"
                }) % (tgl_mulai, tgl_akhir, doc_number)
                payload = payload.replace('\n', '')
                _logger.info("# === CEK PAYLOAD === #")
                _logger.info(payload)

                try:
                    response = requests.request("GET", url_config, data=payload, headers=headers)
                    txt = json.loads(response.text)

                    if txt['DATA']:
                        _logger.info("# === IMPORT DATA === #")
                        company_id = self.env.company.id
                        # _logger.info(txt['DATA'])
                        txt_data0 = sorted(txt['DATA'], key=lambda x: x["DOC_NUMBER"])
                        txt_data = filter(lambda x: (x["STATUS"] == "X"), txt_data0)
                        
                        # txt_data = txt['DATA']
                        for data in txt_data:
                            # _logger.info(data)
                            doc_number = data["DOC_NUMBER"]
                            year = str(data["YEAR"])
                            line_item = data["LINE_ITEM"]
                            amount = data["AMOUNT"]
                            clear_date = data["CLEAR_DATE"]
                            clear_doc = data["CLEAR_DOC"]
                            status = data["STATUS"]
                            new_name = doc_number+str(year)

                            date_format = '%Y-%m-%d'
                            date_from = datetime.strptime(year + '-01-01', date_format)
                            date_to = datetime.strptime(year + '-12-31', date_format)

                            _logger.info("# === CEK ACCOUNT MOVE === #" + year + doc_number )
                            account_move = False
                            account_move1 = self.env['account.move'].search([
                                ('move_type', '=', 'in_invoice'),
                                ('payment_reference', '=', doc_number),
                                ('year', '=', year)], limit=1)
                            if not account_move1:
                                account_move2 = self.env['account.move'].search([
                                    ('move_type', '=', 'in_invoice'),
                                    ('payment_reference', '=', doc_number),
                                    ('date', '>=', date_from), ('date', '<=', date_to)], limit=1)
                                _logger.info("# === ACCOUNT MOVE 2 === #")
                                if account_move2:
                                    account_move = account_move2
                            else:
                                account_move = account_move1
                                
                            _logger.info(account_move)
                            if account_move and account_move.partner_id.company_id.id:
                                account_move.write({
                                    'sap_amount_payment': abs(amount)
                                })
                                account_move._compute_status_payment()

                            else:
                                _logger.info("# === CEK PARTIAL PAYMENT REQUEST === #" + year + doc_number )
                                partial_payment_request = self.env['wika.partial.payment.request'].search([
                                    ('reference', '=', doc_number),
                                    ('year', '=', year)], limit=1)
                                if partial_payment_request and partial_payment_request.partner_id.company_id.id:
                                    sap_amount_payment = partial_payment_request.invoice_id.sap_amount_payment
                                    partial_payment_request.invoice_id.write({
                                        'sap_amount_payment': sap_amount_payment+abs(amount)
                                    })                                
                                    partial_payment_request.invoice_id._compute_status_payment()                                
                                    partial_payment_request.write({
                                        'payment_state': 'paid',
                                        'no_doc_sap': clear_doc
                                    })
                                            
                        rec.state = 'done'
                        _logger.info("# === IMPORT DATA SUKSES === #")
                    else:
                        raise UserError(_("Data Payment Status Tidak Tersedia!"))
                    
                except:
                    # _logger.info("ERRORRRRRRR")
                    # _logger.info(UserError)
                    rec.state = 'not_done'
                    pass

        self.env.ref('wika_integration.get_payment_status')._trigger()
    
   