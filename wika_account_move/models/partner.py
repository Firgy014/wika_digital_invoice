import requests
from odoo import fields, models, api
from odoo.exceptions import UserError

import logging, json
_logger = logging.getLogger(__name__)

class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    bill_coa_type = fields.Selection([
        ('ZN01', 'ZN01 Berelasi'),
        ('ZN02', 'ZN02 Pihak Ketiga'),
        ('ZN03', 'ZN03 Internal'),
        ('ZN04', 'ZN04 KSO'),
        ('ZN05', 'ZN05 JO Non WIKA'),
        ('ZN10', 'ZN10 Customer Individu'),
        ('ZONE', 'ZONE One Time'),
        ('ZV07', 'ZV07 Kas Negara, Leasing'),
        ('ZV08', 'ZV08 Logistik Kapabeanan'),
        ('ZV09', 'ZV09 Perseorangan'),
        ('ZV11', 'ZV11 Vendor Fasilitas Bank'),
    ], string='Bill Chart of Accounts Type')
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
    )

    @api.model
    def _build_vat_error_message(self, country_code, wrong_vat, record_label):
        # Disable VAT format
        pass

    @api.constrains('vat', 'country_id')
    def check_vat(self):
        # Disable VAT format
        pass

    def update_tax(self):
        self.ensure_one()

        kunnr = self.sap_code

        url_config = self.env['wika.integration'].search([('name', '=', 'URL PO')], limit=1)
        url = url_config.url + 'services/auth'
        url_get_partner = url_config.url + 'services/getbpsap'
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "entitas": "FMS",
            "skey": "OAZvRmB7HKDdDkKF29DXZwgSmlv9KqQWZNDWV51SACAbhnOvuA1AvZf5FnIBrLxC"
        })
        payload = payload.replace('\n', '')
        
        # try:
        # 1. Get W-KEY TOKEN
        response = requests.request("POST", url, data=payload, headers=headers)
        w_key = (response.headers['w-key'])
        # _logger.info("# === API GET PARTNER === #")
        # _logger.info(w_key)
        # _logger.info(response)
        csrf = {'w-access-token': str(w_key)}
        headers.update(csrf)
        
        company_id = self.env.company.id
        country_id = self.env.company.country_id.id

        payload = json.dumps({"kunnr": "%s",
                                "taxnum": "",
                                "bp_type": ""
                                }) % (kunnr)
        
        payload = payload.replace('\n', '')
        
        _logger.info(payload)
    
        response_2 = requests.request("POST", url_get_partner, data=payload, headers=headers)
        # _logger.info(response_2.text)
        if response_2.status_code==200:
            txt = json.loads(response_2.text)
            txt_data = txt['data']
            _logger.info("# === TXT DATA === #")
            list_txt_data = []
            if isinstance(txt_data, list):
                list_txt_data = txt_data
            else:
                list_txt_data.append(txt_data)
    
            _logger.info(list_txt_data)
            for data in list_txt_data:
                _logger.info("# === DATA === #")
                # _logger.info(data)
                sap_code = data['LIFNR']
                name = data['NAME1']
                street = data['STREET']
                vat = data['TAXNUM']
                bill_coa_type = data['KTOKK']
                witht = data['WITHT']
                bank_id = 0
                for bank_detail in data['BANK']:
                    bank_name = bank_detail['BANKA']
                    bic = bank_detail['BANKL']
                    acc_number = bank_detail['BANKN']
                    acc_holder_name = bank_detail['KOINH']
                
                    res_bank = self.env['res.bank'].search([
                            ('name', '=', bank_name), 
                            ('active', '=', True)], limit=1)
                    
                    if res_bank:
                        bank_id = res_bank.id
                    else:
                        _logger.info("# === CREATE BANK === #")
                        bank_create = self.env['res.bank'].create({
                            'name': bank_name,
                            'bic': bic,
                            'active': True
                        })
                        _logger.info(bank_create)
                        if bank_create:
                            bank_id = bank_create.id
                    
                    res_bank = self.env['res.bank'].search([
                            ('name', '=', bank_name), 
                            ('active', '=', True)], limit=1)
                    tax_group_names = witht.split(',')
                    # tax_ids = []
                    for tax_group_name in tax_group_names:
                        # _logger.info("# === tax_group_name === #")
                        # _logger.info(tax_group_name)

                        tax_ids = self.env['account.tax.group'].search([('name', '=', tax_group_name)]).wika_tax_ids.mapped('id')
                        if tax_ids:
                            _logger.info("# === tax_ids === #")
                            _logger.info(tax_ids)
                            # self.phone = 1
                            self.update({
                                'phone': 1,
                                'tax_ids': [(6, 0, [x for x in tax_ids])]
                            })
        _logger.info("# === Update TAX Berhasil === #")                            
        # raise UserError("Update Tax Berhasil.")