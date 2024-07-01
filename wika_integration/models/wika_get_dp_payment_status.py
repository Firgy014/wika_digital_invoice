# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning,AccessError
import logging, json
_logger = logging.getLogger(__name__)

class wika_get_dp_payment_status(models.Model):
    _name = 'wika.get.dp.payment.status'
    _description='Wika Get DP Payment Status'

    name = fields.Char(string="Nama")

    current_year = datetime.now().year
    tgl_mulai = fields.Date(string="Tgl Mulai", default=datetime.strptime('%s-01-01' % (current_year),'%Y-%m-%d'))
    tgl_akhir = fields.Date(string="Tgl Akhir", default=datetime.strptime('%s-12-31' % (current_year),'%Y-%m-%d'))

    status=fields.Char(string='Status')

    def _auto_get_dp_payment_status(self, date_from, date_to, doc_number):
        ''' This method is called from a cron job.
        '''
        url_config = self.env['wika.integration'].search([('name', '=', 'URL_DP_PAYMENT_STATUS')], limit=1).url
        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }

        if date_from:
            self.tgl_mulai = date_from

        if date_to:
            self.tgl_akhir = date_to

        payload = json.dumps({
    "COMPANY_CODE": "A000",
    "CLEAR_DATE": {
        "LOW": "2024-06-19",
        "HIGH": "2024-06-19"
    },
    "DOC_NUMBER": "",
    "STATUS": "Y"
}) 
        # % (str(self.tgl_mulai), str(self.tgl_akhir), doc_number)
        payload = payload.replace('\n', '')
        # _logger.info("# === CEK PAYLOAD === #")
        # _logger.info(payload)

        try:
            response = requests.request("GET", url_config, data=payload, headers=headers)
            txt = json.loads(response.text)

            if txt['DATA']:
                _logger.info("# === IMPORT DATA === #")
                company_id = self.env.company.id
                # _logger.info(txt['DATA'])
                txt_data = sorted(txt['DATA'], key=lambda x: x["DOC_NUMBER"])
                # txt_data = txt['DATA']
                for data in txt_data:
                    # _logger.info(data)
                    doc_number = data["DOC_NUMBER"]
                    year = str(data["YEAR"])
                    currency = str(data["CURRENCY"])
                    amount = data["AMOUNT"]
                    pph_cbasis = data["PPH_CBASIS"]
                    ppn = data["PPN"]
                    clear_date = data["CLEAR_DATE"]
                    clear_doc = data["CLEAR_DOC"]
                    vendor = data["VENDOR"]
                    profit_center = data["PROFIT_CENTER"]
                    status = data["STATUS"]
                    
                    _logger.info("# === CEK ACCOUNT MOVE === #" + year + doc_number )
                    account_move = False
                    account_move1 = self.env['account.move'].search([
                        ('move_type', '=', 'in_invoice'),
                        ('bap_id.bap_type', '=', 'uang muka'),
                        ('payment_reference', '=', doc_number),
                        ('status_payment', '!=', 'Paid'),
                        ('year', '=', year)], limit=1)
                    if not account_move1:
                        account_move2 = self.env['account.move'].search([
                            ('move_type', '=', 'in_invoice'),
                            ('bap_id.bap_type', '=', 'uang muka'),
                            ('status_payment', '!=', 'Paid'),
                            ('payment_reference', '=', doc_number),
                            '|', ('date', '>=', self.tgl_mulai), ('date', '<=', self.tgl_akhir)], limit=1)
                        _logger.info("# === ACCOUNT MOVE 2 === #")
                        if account_move2:
                            account_move = account_move2
                    else:
                        account_move = account_move1
                        
                    _logger.info(account_move)
                    if account_move and account_move.partner_id.company_id.id:
                        account_move.write({
                            'status_payment': 'Paid'
                        })

                _logger.info("# === IMPORT DATA SUKSES === #")
            else:
                raise UserError(_("Data Payment Status Tidak Tersedia!"))
            
        except UserError:
            _logger.info("ERRORRRRRRR")
            _logger.info(UserError)
            self.status='-'

        self.env.ref('wika_integration.get_payment_status')._trigger()
    
   