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

    name = fields.Char(string="Nama")
    tgl_mulai = fields.Date(string="Tgl Mulai")
    tgl_akhir = fields.Date(string="Tgl Akhir")
    status=fields.Char(string='Status')

    def _auto_get_payment_status(self, date_from, date_to, doc_number):
        ''' This method is called from a cron job.
        '''
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
        }) % (date_from, date_to, doc_number)
        payload = payload.replace('\n', '')
        # _logger.info("# === CEK PAYLOAD === #")
        # _logger.info(payload)

        # try:
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
                account_move1 = self.env['account.move'].search([('payment_reference', '=', doc_number),
                                                    ('year', '=', year)], limit=1)
                if not account_move1:
                    account_move2 = self.env['account.move'].search([('payment_reference', '=', doc_number),
                                    ('date', '>=', date_from), ('date', '<=', date_to)], limit=1)
                    if account_move2:
                        account_move = account_move2
                else:
                    account_move = account_move1

                if account_move:
                    account_payment = self.env['account.payment'].search([('ref', '=', doc_number),
                                                                            ('date', '=', clear_date)])
                    if not account_payment:
                        _logger.info("# === INSERT PAYMENT === #")
                        account_payment_created = self.env['account.payment'].create({
                            'name': new_name,
                            'date': clear_date,
                            'partner_id': account_move.partner_id.id, 
                            'payment_move_id': account_move.id, 
                            'line_item': line_item, 
                            'amount': abs(amount), 
                            'ref': doc_number,
                            'company_id': company_id,
                            'payment_type': 'inbound',
                            'partner_type': 'supplier'
                        })

                        if account_payment_created:
                            # _logger.info("# === ACCOUNT MOVE CREATED === #")
                            # payment_id = account_payment_created.id
                            # _logger.info("# === PAYMENT ID === #" + str(payment_id))
                            account_move.write({'payment_id': account_payment_created.id})
                            account_move._compute_amount_due()
                            account_move.action_post()
                else:
                    _logger.info("# === CEK PARTIAL PAYMENT REQUEST === #" + year + doc_number )
                    partial_payment_request = self.env['wika.partial.payment.request'].search([
                        ('reference', '=', doc_number),
                        ('year', '=', year)], limit=1)
                    if partial_payment_request:
                        _logger.info("# === INSERT PAYMENT === #")
                        _logger.info(partial_payment_request)
                        account_payment = self.env['account.payment'].search([('ref', '=', doc_number),
                                                                            ('date', '=', clear_date)])
                        if not account_payment:
                            account_payment_created = self.env['account.payment'].create({
                                'name': new_name,
                                'date': clear_date,
                                'partner_id': partial_payment_request.partner_id.id,
                                'payment_move_id': account_move.id,  
                                'line_item': line_item, 
                                'amount': abs(amount), 
                                'ref': doc_number,
                                'company_id': company_id,
                                'payment_type': 'inbound',
                                'partner_type': 'supplier'
                            })

                            if account_payment_created:
                                # _logger.info("ADA")
                                payment_id = account_payment_created.id
                                partial_payment_request.invoice_id.write({'payment_id': payment_id})
                                partial_payment_request.invoice_id._compute_amount_due()
                                partial_payment_request.invoice_id.action_post()
                                partial_payment_request.write({'payment_state': 'paid',
                                                                'payment_id': payment_id,
                                                                'no_doc_sap': clear_doc
                                                                })

            _logger.info("# === IMPORT DATA SUKSES === #")
        else:
            raise UserError(_("Data Payment Status Tidak Tersedia!"))
            
        # except UserError:
        #     _logger.info("ERRORRRRRRR")
        #     _logger.info(UserError)
        #     self.status='-'

        self.env.ref('wika_integration.get_payment_status')._trigger()
    
   