# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError, Warning,AccessError
import logging, json
_logger = logging.getLogger(__name__)

class wika_get_po(models.Model):
    _name = 'wika.get.po'
    _description='Wika Get Integration'

    profit_center = fields.Char(string="Profit Center")
    name = fields.Char(string="Nomor PO")
    jenis = fields.Char(string="Jenis")
    po_plant = fields.Char(string="PO Plant")
    co_code = fields.Char(string="Co Code")
    status=fields.Char(string='Status')
    tgl_create_sap=fields.Date(string='Tanggal Create SAP')
    tgl_write_sap = fields.Date(string='Tanggal Update SAP')

    def _auto_update_create_po(self, max_difference_days):
        ''' This method is called from a cron job.
        It is used to post entries such as those created by the module
        account_asset and recurring entries created in _post().
        '''
        records = self.search([])
        # Ambil nilai max_difference_days dari context
        for ids in self._cr.split_for_in_conditions(records.ids, size=100):
            moves = self.browse(ids)
            try:  # try posting in batch
                with self.env.cr.savepoint():
                    moves.get_po_schedule2(max_difference_days=max_difference_days)  # Mengirimkan parameter dari context


            except UserError:  # if at least one move cannot be posted, handle moves one by one
                for move in moves:
                    try:
                        with self.env.cr.savepoint():
                            move.get_po_schedule2(max_difference_days=max_difference_days)  # Mengirimkan parameter dari context
                    except:
                        pass

        # if len(records) == 100:  # assumes there are more whenever search hits limit
        self.env.ref('wika_integration.update_create_po_actions')._trigger()
    
    def get_po_schedule2(self, max_difference_days):
        url_config = self.env['wika.integration'].search([('name', '=', 'URL PO')], limit=1)
        url = url_config.url + 'services/auth'
        url_get_po = url_config.url + 'services/getposap'
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
        # _logger.info("DEBUG: =================================================================================")
        # _logger.info(w_key)
        csrf = {'w-access-token': str(w_key)}
        headers.update(csrf)

        records = self.search([])
        # records = self.search([('jenis', '=', 'debug')])
        
        # _logger.info(response)
        company_id = self.env.company.id
        i = 0
        tot_i = 0
        tot_u = 0 
        for record in records:
            tgl_update=fields.Date.today() + timedelta(days=int(max_difference_days)*-1)
            if record.profit_center:
                profit_center = record.profit_center
            else:
                profit_center = ''

            if record.name:
                no_po = record.name
            else:
                no_po = ''
            if record.tgl_create_sap:
                tgl_create_sap = record.tgl_create_sap
            else:
                tgl_create_sap =  str(tgl_update)

            if record.tgl_write_sap:
                tgl_write_sap = record.tgl_write_sap
            else:
                tgl_write_sap =  str(tgl_update)

            payload_2 = json.dumps({"profit_center": "%s",
                                    "po_doc": "%s",
                                    "po_jenis": "",
                                    "po_dcdat": "",
                                    "po_crdate": "",
                                    "po_plant": "",
                                    "co_code": "",
                                    "po_del": "",
                                    "poitem_del": "",
                                    "incmp_cat": "",
                                    "po_lcdat": "%s"
                                    }) % (profit_center, no_po, tgl_write_sap)
            payload_2 = payload_2.replace('\n', '')
            
            _logger.info(payload_2)
        
            response_2 = requests.request("POST", url_get_po, data=payload_2, headers=headers)
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
                    _logger.info("# === IMPORT DATA === #")
                    _logger.info(data)
                    vals = []
                    potongan = []
                    po = self.env['purchase.order'].search([
                        ('name', '=', data['po_doc']), ('tgl_create_sap', '=', data['po_crdat']),
                        ('state', '!=', 'cancel')], limit=1)
                    _logger.info("# === PO === #")
                    # _logger.info(data)
                    if not po:
                        _logger.info("# === CREATE PO === #")
                        _logger.info(data)
                        dp = float(data['dp_amt'])
                        retensi = float(data['ret_pc'])
                        if 'pay_terms' in data and data['pay_terms'] != '':
                            payment_term = self.env['account.payment.term'].sudo().search([
                                ('name', '=', data['pay_terms'])], limit=1)
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
                        
                        # Looping pengisian data detail po
                        for hasil in data['isi']:
                            _logger.info("# === DEBUG DETAIL === #")
                            seq = float(hasil['po_no'])
                            line_active = True
                            state = 'po'
                            
                            qty = float(hasil['po_qty'])
                            if data['po_jenis'] == 'JASA':
                                price = float(hasil['po_price']) / qty
                            else:
                                price = float(hasil['po_price'])
                            _logger.info("# === PRICE === #")
                            _logger.info("price")

                            _logger.info("# === SEARCH PRODUCT === #")
                            prod = self.env['product.product'].sudo().search([
                                ('default_code', '=', hasil['prd_no'])], limit=1)
                            _logger.info(prod)
                            if prod:
                                product_id = prod.id
                            else:
                                _logger.info("# === CREATE PRODUCT === #")
                                _logger.info(hasil['prd_no'])
                                product_id = self.env['product.product'].create({
                                                'name': hasil['prd_no'],
                                                'list_price': price,
                                                'standard_price': price,
                                                'type': 'consu',
                                            }).id
                                # prod = self.env['product.product'].sudo().create({
                                #     ('name', '=', hasil['prd_no']), ('default_code', '=', hasil['prd_no'])})
                                _logger.info(product_id)

                            _logger.info(prod)    
                            
                            
                            tax = self.env['account.tax'].sudo().search([
                                ('name', '=', hasil['tax_code'])], limit=1)
                            if not tax:
                                return "Kode Pajak  : %s tidak ditemukan" % hasil['MWSKZ']
                            
                            _logger.info("# === TAX === #")
                            _logger.info(tax)
                            curr = self.env['res.currency'].sudo().search([
                                ('name', '=', data['curr'])], limit=1)
                            _logger.info("# === CURRENCY === #")
                            _logger.info(curr)
                            if not curr:
                                continue
                            
                            vendor = self.env['res.partner'].sudo().search([
                                ('sap_code', '=', data['vendor'])], limit=1)
                            _logger.info("# === VENDOR === #")
                            _logger.info(vendor)
                            if not vendor:
                                vendor = self.get_partner(data['vendor'], '', '')

                            
                                
                            sql = """
                                SELECT 
                                    id
                                FROM uom_uom uom
                                WHERE 
                                    COALESCE(uom.name->>'en_US', uom.name->>'en_US') = '""" + str(hasil['po_uom']) + """'
                            """
                            # _logger.info(sql)
                            self._cr.execute(sql)
                            uoms = self._cr.fetchall()
                            
                            # _logger.info(uoms[0][0])
                            uom = self.env['uom.uom'].browse(uoms[0][0])
                            # uom = self.env['uom.uom'].sudo().search([
                            #     ('name', '=', hasil['po_uom'])], limit=1)
                            _logger.info("# === UOM === #")
                            _logger.info(uom)
                            if not uom:
                                uom = self.env['uom.uom'].sudo().create({
                                    'name': hasil['po_uom'], 'category_id': 1})
                                
                            project = self.env['project.project'].search([
                                ('sap_code', '=', data['prctr']), ('company_id', '=', company_id)], limit=1)
                            if project:
                                project_id = project.id
                                branch_id = project.branch_id.id
                                department_id = None
                            
                            if not project:
                                branch = self.env['res.branch'].sudo().search([
                                    ('sap_code', '=', data['prctr']), ('company_id', '=', company_id)], limit=1)
                                if branch and branch.biro == True:
                                    department_id = branch.id
                                    branch_id = branch.parent_id.id
                                    project_id = None
                                if branch and branch.biro == False:
                                    department_id = None
                                    branch_id = branch.id
                                    project_id = None
                                if not branch:
                                    _logger.info("Kode Profit Center : %s tidak ditemukan" % data['prctr'])
                                
                            if hasil['poitem_del'] == 'L':
                                line_active = False

                            vals.append((0, 0, {
                                'sequence': int(seq),
                                'product_id': product_id,
                                'product_qty': qty,
                                'product_uom': uom.id,
                                'price_unit': price,
                                'active': line_active,
                                'taxes_id': [(6, 0, [x.id for x in tax])]

                            }))
                        
                        if not vals:
                            continue
                        else:
                            po_create = self.env['purchase.order'].sudo().create({
                                'name': data['po_doc'],
                                'payment_term_id': payment_term.id if payment_term else False,
                                'partner_id': vendor.id if vendor else False,
                                'project_id': project_id,
                                'branch_id': branch_id,
                                'department_id': department_id,
                                'order_line': vals,
                                'price_cut_ids': potongan,
                                'currency_id': curr.id,
                                'begin_date': data['po_dcdat'],
                                'po_type': data['po_jenis'],
                                'state': state,
                                'tgl_create_sap': data['po_crdat']

                            })
                            _logger.info("# === PO CREATED === #")
                            _logger.info(po_create)
                            # po_create.get_gr()
                            tot_i += 1
                    
                    else: # Update PO
                        _logger.info("# === UPDATE PO === #")
                        _logger.info(po)
                        current_date = fields.Date.today()
                        po_lcdat = datetime.strptime(data['po_lcdat'], '%Y-%m-%d').date()
                        difference = current_date - po_lcdat
                        if difference.days == max_difference_days:
                            for hasil in data['isi']:
                                seq = float(hasil['po_no'])
                                qty = float(hasil['po_qty'])
                                po_line = self.env['purchase.order.line'].sudo().search([
                                    ('order_id', '=', po.id),
                                    ('sequence', '=', int(seq))], limit=1)
                                _logger.info("# === PO LINE ID === #")
                                _logger.info(po_line.id)
                                current_datetime_str = fields.Datetime.now()+ timedelta(hours=7)

                                noted_message = f"updated {current_datetime_str}"
                                po.write({'notes': noted_message})
                                
                                if po_line.id:
                                    _logger.info("# === WRITE PO === #")
                                    if data['po_jenis'] == 'JASA':
                                        price = float(hasil['po_price']) / qty
                                    else:
                                        price = float(hasil['po_price'])

                                    tax = self.env['account.tax'].sudo().search([
                                        ('name', '=', hasil['tax_code'])], limit=1)
                                    if not tax:
                                        _logger.info("Kode Pajak  : %s tidak ditemukan" % hasil['MWSKZ'])
                                    
                                    if hasil['poitem_del'] == 'L':
                                        po_line.write({'active': False})
                                    else:    
                                        po_line.write({'product_qty': qty,'price_unit':price,'taxes_id': [(6, 0, [x.id for x in tax])]})

                                else:
                                    if hasil['poitem_del'] == 'L':
                                        continue
                                    else:
                                        if data['po_jenis'] == 'JASA':
                                            price = float(hasil['po_price']) / qty
                                        else:
                                            price = float(hasil['po_price'])
                                        prod = self.env['product.product'].sudo().search([
                                            ('default_code', '=', hasil['prd_no'])], limit=1)
                                        if not prod:
                                            prod = self.env['product.product'].sudo().create({
                                                'name': hasil['prd_desc'],'default_code':hasil['prd_no']})
                                        tax = self.env['account.tax'].sudo().search([
                                            ('name', '=', hasil['tax_code'])], limit=1)
                                        if not tax:
                                            return "Kode Pajak  : %s tidak ditemukan" % hasil['MWSKZ']

                                        uom = self.env['uom.uom'].sudo().search([
                                            ('name', '=', hasil['po_uom'])], limit=1)
                                        if not uom:
                                            uom = self.env['uom.uom'].sudo().create({
                                                'name': hasil['po_uom'], 'category_id': 1})
                                        line = self.env['purchase.order.line'].sudo().create({
                                                'order_id':po.id,
                                                'sequence': int(seq),
                                                'product_id': prod.id if prod else False,
                                                'product_qty': qty,
                                                'product_uom': uom.id,
                                                'price_unit': price,
                                                'taxes_id': [(6, 0, [x.id for x in tax])]})

                                    continue

                            # po.update_gr()
                            tot_u += 1
                            
                    i += 1

        _logger.info("# === IMPORT DATA BERHASIL === # %s %s %s" % (str(i), str(tot_i), str(tot_u)))
        # except:
        #     pass
 
    def get_partner(self, kunnr, taxnum, bp_type):
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
                                "taxnum": "%s",
                                "bp_type": "%s"
                                }) % (kunnr, taxnum, bp_type)
        
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
                        if bank_create:
                            bank_id = bank_create.id

                res_partner = self.env['res.partner'].search([('sap_code', '=', sap_code)], limit=1)
                res_partner_id = 0
                if res_partner:
                    res_partner_id = res_partner.id
                else:
                    res_partner_create = self.env['res.partner'].create({
                        'name': name,
                        'sap_code': sap_code,
                        'street': street,
                        'vat': vat,
                        'bill_coa_type': bill_coa_type,
                        'company_id': company_id,
                        'country_id': country_id,
                        'is_company': True,
                    })
                    if res_partner_create:
                        res_partner_id = res_partner_create.id
                        res_partner_bank_create = self.env['res.partner.bank'].create({
                            'partner_id': res_partner_id,  
                            'bank_id': bank_id,  
                            'acc_number': acc_number,
                            'acc_holder_name': acc_holder_name,
                            'company_id': company_id
                        })


            return res_partner_id
                     
    def _autocreate_po(self):
        ''' This method is called from a cron job.
        It is used to post entries such as those created by the module
        account_asset and recurring entries created in _post().
        '''
        records = self.search([])
        # Ambil nilai max_difference_days dari context
        for ids in self._cr.split_for_in_conditions(records.ids, size=100):
            moves = self.browse(ids)
            try:  # try posting in batch
                with self.env.cr.savepoint():
                    moves.get_po_schedule()  # Mengirimkan parameter dari context


            except UserError:  # if at least one move cannot be posted, handle moves one by one
                for move in moves:
                    try:
                        with self.env.cr.savepoint():
                            move.get_po_schedule()  # Mengirimkan parameter dari context
                    except:
                        pass

        # if len(records) == 100:  # assumes there are more whenever search hits limit
        self.env.ref('wika_integration.create_po_actions')._trigger()

    def get_po_schedule(self):
        url_config = self.env['wika.integration'].search([('name', '=', 'URL PO')], limit=1)
        url = url_config.url + 'services/auth'
        url_get_po = url_config.url + 'services/getposap'
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "entitas": "FMS",
            "skey": "OAZvRmB7HKDdDkKF29DXZwgSmlv9KqQWZNDWV51SACAbhnOvuA1AvZf5FnIBrLxC"
        })
        payload = payload.replace('\n', '')
        print ("000000000000000000000000000000000000000000000")
        try:
            # 1. Get W-KEY TOKEN
            response = requests.request("POST", url, data=payload, headers=headers)
            w_key = (response.headers['w-key'])
            csrf = {'w-access-token': str(w_key)}
            headers.update(csrf)

            for record in self:
                tgl_update=fields.Date.today() + timedelta(days=-1)
                if record.profit_center:
                    profit_center = record.profit_center
                else:
                    profit_center = ''

                if record.name:
                    no_po = record.name
                else:
                    no_po = ''
                if record.tgl_create_sap:
                    tgl_create_sap = record.tgl_create_sap
                else:
                    tgl_create_sap =  str(tgl_update)
                payload_2 = json.dumps({"profit_center": "%s",
                                        "po_doc": "%s",
                                        "po_jenis": "",
                                        "po_dcdat": "",
                                        "po_crdate": "%s",
                                        "po_plant": "%s",
                                        "co_code": "%s",
                                        "po_del": "",
                                        "poitem_del": "",
                                        "incmp_cat": "",
                                        "po_lcdat": ""
                                        }) % (profit_center, no_po, tgl_create_sap,record.po_plant, record.co_code)
                payload_2 = payload_2.replace('\n', '')
                _logger.info(payload_2)
                response_2 = requests.request("POST", url_get_po, data=payload_2, headers=headers)
                # print("RRRRRRRRRRRRRRRRRRRRRRRRRR",response_2.status_code)
                # print("RRRRRRRRRRRRRRRRRRRRRRRRRR",response_2.status_code)
                if response_2.status_code==200:
                    txt = json.loads(response_2.text)
                    print(txt['data'])
                    if txt['data']:
                        txt_data = txt['data']
                        if isinstance(txt_data, list):
                            # print ("1111111111111111111")
                            # print ("1111111111111111111")
                            for data in txt_data:
                                vals = []
                                potongan = []
                                # if data['po_del'] == 'C':
                                #     po = self.env['purchase.order'].sudo().search([
                                #         ('name', '=', data['po_doc']), ('tgl_create_sap', '=', data['po_crdat']),
                                #         ('state', '!=', 'cancel')], limit=1)
                                #     if po:
                                #         po.write({'state': 'cancel', 'active': False})
                                #else:
                                po = self.env['purchase.order'].sudo().search([
                                    ('name', '=', data['po_doc']), ('tgl_create_sap', '=', data['po_crdat']),
                                    ('state', '!=', 'cancel')], limit=1)
                                if not po:
                                    print (data['po_doc'])
                                    dp = float(data['dp_amt'])
                                    retensi = float(data['ret_pc'])
                                    if 'pay_terms' in data and data['pay_terms'] != '':
                                        payment_term = self.env['account.payment.term'].sudo().search([
                                            ('name', '=', data['pay_terms'])], limit=1)
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
                                    for hasil in data['isi']:
                                        seq = float(hasil['po_no'])
                                        line_active = True
                                        state = 'po'
                                        print ("mmmmmmmmmmmmmmmm")
                                        prod = self.env['product.product'].sudo().search([
                                            ('default_code', '=', hasil['prd_no'])], limit=1)
                                        print(prod)
                                        qty = float(hasil['po_qty'])
                                        print(data['po_jenis'])
                                        if data['po_jenis'] == 'JASA':
                                            price = float(hasil['po_price']) / qty
                                        else:
                                            price = float(hasil['po_price'])
                                        if not prod:
                                            prod = self.env['product.product'].sudo().create({
                                                ('name', '=', hasil['prd_no']), ('default_code', '=', hasil['prd_no'])})
                                        print ("kkkkkkkkkkkkkkkkkkkkkk")
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
                                            continue
                                            # return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
                                        uom = self.env['uom.uom'].sudo().search([
                                            ('name', '=', hasil['po_uom'])], limit=1)
                                        if not uom:
                                            uom = self.env['uom.uom'].sudo().create({
                                                'name': hasil['po_uom'], 'category_id': 1})
                                        project = self.env['project.project'].sudo().search([
                                            ('sap_code', '=', data['prctr']), ('company_id', '=', 1)], limit=1)
                                        if project:
                                            profit_center = project.id
                                            branch_id = project.branch_id.id
                                            department_id = None
                                        print ("llllllllllllllllllllll")
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
                                        # print ("[[[[[[[[[[[[[[[[[[")
                                        # print ("[[[[[[[[[[[[[[[[[[")
                                        vals.append((0, 0, {
                                            'sequence': int(seq),
                                            'product_id': prod.id if prod else False,
                                            'product_qty': qty,
                                            'product_uom': uom.id,
                                            'price_unit': price,
                                            'active': line_active,
                                            'taxes_id': [(6, 0, [x.id for x in tax])]

                                        }))
                                        print (vals)
                                else:
                                    # print ("SSSSSSSSSSSSSSSSSSSSS")
                                    # print ("SSSSSSSSSSSSSSSSSSSSS")

                                    for hasil in data['isi']:
                                        seq = float(hasil['po_no'])
                                        po_line = self.env['purchase.order.line'].sudo().search([
                                            ('sequence', '=', int(seq))], limit=1)
                                        if po_line and hasil['poitem_del'] == 'L':
                                            po_line.write({'active': False})

                                if not vals:
                                    continue
                                else:
                                    # print ("DDDDDDDDDDDDD")
                                    # print ("DDDDDDDDDDDDD")
                                    po_create = self.env['purchase.order'].sudo().create({
                                        'name': data['po_doc'],
                                        'payment_term_id': payment_term.id if payment_term else False,
                                        'partner_id': vendor.id if vendor else False,
                                        'project_id': profit_center,
                                        'branch_id': branch_id,
                                        'department_id': department_id,
                                        'order_line': vals,
                                        'price_cut_ids': potongan,
                                        'currency_id': curr.id,
                                        'begin_date': data['po_dcdat'],
                                        'po_type': data['po_jenis'],
                                        'state': state,
                                        'tgl_create_sap': data['po_crdat']

                                    })
                                    po_create.get_gr()
                        else:
                            # print("22222222222222222")
                            # print("22222222222222222")
                            vals = []
                            potongan = []
                            # if txt_data['po_del'] == 'C':
                            #     po = self.env['purchase.order'].sudo().search([
                            #         ('name', '=', txt_data['po_doc']), ('tgl_create_sap', '=', txt_data['po_crdat']),
                            #         ('state', '!=', 'cancel')], limit=1)
                            #     if po:
                            #         po.write({'state': 'cancel', 'active': False})
                            #else:
                            po = self.env['purchase.order'].sudo().search([
                                ('name', '=', txt_data['po_doc']), ('tgl_create_sap', '=', txt_data['po_crdat']),
                                ('state', '!=', 'cancel')], limit=1)
                            if not po:
                                dp = float(txt_data['dp_amt'])
                                retensi = float(txt_data['ret_pc'])
                                if txt_data['pay_terms'] != '':
                                    payment_term = self.env['account.payment.term'].sudo().search([
                                        ('name', '=', txt_data['pay_terms'])], limit=1)

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
                                    line_active = True

                                    state = 'po'

                                    prod = self.env['product.product'].sudo().search([
                                        ('default_code', '=', data['prd_no'])], limit=1)
                                    qty = float(data['po_qty'])
                                    print("qty awal-------------------------------", qty)
                                    if txt_data['po_jenis'] == 'JASA':
                                        price = float(data['po_price']) / qty
                                    else:
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
                                        continue
                                        # return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
                                    uom = self.env['uom.uom'].sudo().search([
                                        ('name', '=', data['po_uom'])], limit=1)
                                    if not uom:
                                        uom = self.env['uom.uom'].sudo().create({
                                            'name': data['po_uom'], 'category_id': 1})
                                    project = self.env['project.project'].sudo().search([
                                        ('sap_code', '=', txt_data['prctr']), ('company_id', '=', 1)], limit=1)
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
                                        line_active = False
                                    vals.append((0, 0, {
                                        'sequence': int(seq),
                                        'product_id': prod.id if prod else False,
                                        'product_qty': qty,
                                        'product_uom': uom.id,
                                        'price_unit': price,
                                        'active': line_active,
                                        'taxes_id': [(6, 0, [x.id for x in tax])]

                                    }))
                                    print("ppppppppp", vals)
                            else:
                                for data in txt_data['isi']:
                                    seq = float(data['po_no'])
                                    po_line = self.env['purchase.order.line'].sudo().search([
                                        ('sequence', '=', int(seq))], limit=1)
                                    if po_line and data['poitem_del'] == 'L':
                                        po_line.write({'active': False})

                            if vals:
                                po_create = self.env['purchase.order'].sudo().create({
                                    'name': txt_data['po_doc'],
                                    'payment_term_id': payment_term.id if payment_term else False,
                                    'partner_id': vendor.id if vendor else False,
                                    'project_id': profit_center,
                                    'branch_id': branch_id,
                                    'department_id': department_id,
                                    'order_line': vals,
                                    'price_cut_ids': potongan,
                                    'currency_id': curr.id,
                                    'begin_date': txt_data['po_dcdat'],
                                    'po_type': txt_data['po_jenis'],
                                    'state': state,
                                    'tgl_create_sap': txt_data['po_crdat']

                                })
                                po_create.get_gr()
                        self.status = 'OK'
                    else:
                        raise UserError(_("Data PO Tidak Tersedia!"))

                else:
                    pass
        except:
            pass

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

            payload_2 = json.dumps({"profit_center" : "%s",
            "po_doc" : "%s",
            "po_jenis" : "",
            "po_dcdat" : "",
            "po_crdate": "",
            "po_plant" : "%s",
            "co_code" : "%s",
            "po_del" : "",
            "poitem_del" : "",
            "incmp_cat" : "","po_lcdat":""
        }) % (self.profit_center, self.name, self.po_plant, self.co_code)
            payload_2 = payload_2.replace('\n', '')
            # _logger.info(payload_2)
            # _logger.info(payload_2)
            response_2 = requests.request("POST", url_get_po, data=payload_2, headers=headers)
            txt = json.loads(response_2.text)
            if txt['data']:
                txt_data = txt['data']
                if isinstance(txt_data, list):
                    for data in txt_data:
                        vals = []
                        potongan = []
                        if data['po_del'] == 'C':
                            po = self.env['purchase.order'].sudo().search([
                                ('name', '=', data['po_doc']), ('tgl_create_sap', '=', data['po_crdat']),
                                ('state', '!=', 'cancel')], limit=1)
                            if po:
                                po.write({'state': 'cancel', 'active': False})
                        else:
                            po = self.env['purchase.order'].sudo().search([
                                ('name', '=', data['po_doc']), ('tgl_create_sap', '=', data['po_crdat']),
                                ('state', '!=', 'cancel')], limit=1)
                            if not po:
                                dp = float(data['dp_amt'])
                                retensi = float(data['ret_pc'])
                                if 'pay_terms' in txt_data and txt_data['pay_terms'] != '':
                                    payment_term = self.env['account.payment.term'].sudo().search([
                                        ('name', '=', txt_data['pay_terms'])], limit=1)
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
                                for hasil in data['isi']:
                                    seq = float(hasil['po_no'])
                                    line_active = True
                                    state = 'po'

                                    prod = self.env['product.product'].sudo().search([
                                        ('default_code', '=', hasil['prd_no'])], limit=1)

                                    qty = float(data['po_qty'])
                                    print("qty awalfffffffffffffff-------------------------------", qty)
                                    if txt_data['po_jenis'] == 'JASA':
                                        price = float(data['po_price']) / qty
                                    else:
                                        price = float(data['po_price'])
                                    if not prod:
                                        prod = self.env['product.product'].sudo().create({
                                            ('name', '=', hasil['prd_no']), ('default_code', '=', hasil['prd_no'])})

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
                                        continue
                                        # return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
                                    uom = self.env['uom.uom'].sudo().search([
                                        ('name', '=', hasil['po_uom'])], limit=1)
                                    if not uom:
                                        uom = self.env['uom.uom'].sudo().create({
                                            'name': hasil['po_uom'], 'category_id': 1})
                                    project = self.env['project.project'].sudo().search([
                                        ('sap_code', '=', data['prctr']), ('company_id', '=', 1)], limit=1)
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
                                        'active': line_active,
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
                                    'payment_term_id': payment_term.id if payment_term else False,
                                    'partner_id': vendor.id if vendor else False,
                                    'project_id': profit_center,
                                    'branch_id': branch_id,
                                    'department_id': department_id,
                                    'order_line': vals,
                                    'price_cut_ids': potongan,
                                    'currency_id': curr.id,
                                    'begin_date': data['po_dcdat'],
                                    'po_type': data['po_jenis'],
                                    'state': state,
                                    'tgl_create_sap': data['po_crdat']

                                })
                                po_create.get_gr()
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
                            if txt_data['pay_terms'] != '':
                                payment_term = self.env['account.payment.term'].sudo().search([
                                    ('name', '=', txt_data['pay_terms'])], limit=1)

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
                                line_active = True

                                state = 'po'

                                prod = self.env['product.product'].sudo().search([
                                    ('default_code', '=', data['prd_no'])], limit=1)
                                qty = float(data['po_qty'])
                                print("qty awal-------------------------------", qty)
                                if txt_data['po_jenis'] == 'JASA':
                                    price = float(data['po_price']) / qty
                                else:
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
                                    continue
                                    # return "Vendor  : %s tidak ditemukan" % hasil['LIFNR']
                                uom = self.env['uom.uom'].sudo().search([
                                    ('name', '=', data['po_uom'])], limit=1)
                                if not uom:
                                    uom = self.env['uom.uom'].sudo().create({
                                        'name': data['po_uom'], 'category_id': 1})
                                project = self.env['project.project'].sudo().search([
                                    ('sap_code', '=', txt_data['prctr']), ('company_id', '=', 1)], limit=1)
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
                                    line_active = False
                                vals.append((0, 0, {
                                    'sequence': int(seq),
                                    'product_id': prod.id if prod else False,
                                    'product_qty': qty,
                                    'product_uom': uom.id,
                                    'price_unit': price,
                                    'active': line_active,
                                    'taxes_id': [(6, 0, [x.id for x in tax])]

                                }))
                                print("ppppppppp", vals)
                        else:
                            for data in txt_data['isi']:
                                seq = float(data['po_no'])
                                po_line = self.env['purchase.order.line'].sudo().search([
                                    ('sequence', '=', int(seq))], limit=1)
                                if po_line and data['poitem_del'] == 'L':
                                    po_line.write({'active': False})

                        if vals:
                            po_create = self.env['purchase.order'].sudo().create({
                                'name': txt_data['po_doc'],
                                'payment_term_id': payment_term.id if payment_term else False,
                                'partner_id': vendor.id if vendor else False,
                                'project_id': profit_center,
                                'branch_id': branch_id,
                                'department_id': department_id,
                                'order_line': vals,
                                'price_cut_ids': potongan,
                                'currency_id': curr.id,
                                'begin_date': txt_data['po_dcdat'],
                                'po_type': txt_data['po_jenis'],
                                'state': state,
                                'tgl_create_sap': txt_data['po_crdat']

                            })
                            po_create.get_gr()
                self.status = 'OK'
            else:
                raise UserError(_("Data PO Tidak Tersedia!"))
        except:
            pass

    def assign_todo_first(self):
        model_model = self.env['ir.model'].sudo()
        document_setting_model = self.env['wika.document.setting'].sudo()
        model_id = model_model.search([('model', '=', 'purchase.order')], limit=1)
        po = self.env['purchase.order'].search([('name', '=', self.name)], limit=1)

        for res in po:
            level=res.level
            first_user = False
            if level:
                approval_id = self.env['wika.approval.setting'].sudo().search(
                    [('model_id', '=', model_id.id), ('level', '=', level),('transaction_type','=',res.transaction_type)], limit=1)
                approval_line_id = self.env['wika.approval.setting.line'].search([
                    ('sequence', '=', 1),
                    ('approval_id', '=', approval_id.id)
                ], limit=1)
                groups_id = approval_line_id.groups_id
                if groups_id:
                    for x in groups_id.users:
                        if level == 'Proyek' and x.project_id == res.project_id:
                            first_user = x.id
                        if level == 'Divisi Operasi' and x.branch_id == res.branch_id:
                            first_user = x.id
                        if level == 'Divisi Fungsi' and x.department_id == res.department_id:
                            first_user = x.id
                print(first_user)
                #     # Createtodoactivity
                if first_user:
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': 4,
                        'res_model_id': model_id.id,
                        'res_id': res.id,
                        'user_id': first_user,
                        'nomor_po': res.name,
                        'date_deadline': fields.Date.today() + timedelta(days=5),
                        'state': 'planned',
                        'summary': f"Need Upload Document {model_id.name}!"
                    })
            # Get Document Setting
            document_list = []
            doc_setting_id = document_setting_model.search([('model_id', '=', model_id.id)])
            self.status="Assign"

            if doc_setting_id:
                for document_line in doc_setting_id:
                    document_list.append((0, 0, {
                        'purchase_id': res.id,
                        'document_id': document_line.id,
                        'state': 'waiting'
                    }))
                res.document_ids = document_list
            else:
                raise AccessError(
                    "Either approval and/or document settings are not found. Please configure it first in the settings menu.")

class paymentall_ncl_class(models.TransientModel):
    """
    This wizard will confirm the all the selected no.swift
    """

    _name = "wika.get.po.all"
    _description = "Get PO Selected"

    def get_po_all(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['wika.get.po'].browse(active_ids):
            record.get_po()
        return {'type': 'ir.actions.act_window_close'}


