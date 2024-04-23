from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError
import requests
import logging, json
_logger = logging.getLogger(__name__)
from datetime import date, datetime, timedelta
class Purchase_Order(models.Model):
    _inherit='purchase.order'

    def _autoupdate_po(self,max_difference_days):
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
                    moves.update_po_schedule(max_difference_days=max_difference_days)  # Mengirimkan parameter dari context


            except UserError:  # if at least one move cannot be posted, handle moves one by one
                for move in moves:
                    try:
                        with self.env.cr.savepoint():
                            move.update_po_schedule(
                                max_difference_days=max_difference_days)  # Mengirimkan parameter dari context
                    except:
                        pass

        # if len(records) == 100:  # assumes there are more whenever search hits limit
        self.env.ref('wika_integration.get_po_actions')._trigger()

    def update_po_schedule(self,max_difference_days):
        url_config = self.env['wika.integration'].search([('name', '=', 'URL PO')], limit=1)
        url = url_config.url + 'services/auth'
        url_get_po = url_config.url + 'services/getposap'
        # print (url)
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "entitas": "FMS",
            "skey": "OAZvRmB7HKDdDkKF29DXZwgSmlv9KqQWZNDWV51SACAbhnOvuA1AvZf5FnIBrLxC"
        })
        payload = payload.replace('\n', '')

        try:
            # 1. Get W-KEY TOKEN
            response = requests.request("POST", url, data=payload, headers=headers)
            w_key = (response.headers['w-key'])
            csrf = {'w-access-token': str(w_key)}
            headers.update(csrf)
            for record in self:
                if record.project_id:
                    profit_center=record.project_id.sap_code
                else:
                    profit_center=record.branch_id.sap_code
                payload_2 = json.dumps({"profit_center": "%s",
                                        "po_doc": "%s",
                                        "po_jenis": "",
                                        "po_dcdat": "",
                                        "po_crdate": "%s",
                                        "po_plant": "A000",
                                        "co_code": "A000",
                                        "po_del": "",
                                        "poitem_del": "",
                                        "incmp_cat": "","po_lcdat":""
                                        }) % (profit_center, record.name,record.tgl_create_sap)
                payload_2 = payload_2.replace('\n', '')
                current_date = fields.Date.today()
                _logger.info(current_date)
                response_2 = requests.request("POST", url_get_po, data=payload_2, headers=headers)
                _logger.info(response_2)
                txt = json.loads(response_2.text)
                if 'data' in txt:
                    if txt['data']:
                        txt_data = txt['data']
                        vals = []
                        po_lcdat = datetime.strptime(txt_data['po_lcdat'], '%Y-%m-%d').date()
                        difference = current_date - po_lcdat
                        if difference.days == max_difference_days:
                            print (record.name)
                            for data in txt_data['isi']:
                                seq = float(data['po_no'])
                                qty = float(data['po_qty'])
                                po_line = self.env['purchase.order.line'].sudo().search([
                                    ('order_id', '=', record.id),
                                    ('sequence', '=', int(seq))], limit=1)
                                current_datetime_str = fields.Datetime.now()+ timedelta(hours=7)

                                noted_message = f"updated {current_datetime_str}"
                                record.write({'notes': noted_message})


                                if po_line.id:
                                    if txt_data['po_jenis'] == 'JASA':
                                        price = float(data['po_price']) / qty
                                    else:
                                        price = float(data['po_price'])
                                    tax = self.env['account.tax'].sudo().search([
                                        ('name', '=', data['tax_code'])], limit=1)
                                    if not tax:
                                        return "Kode Pajak  : %s tidak ditemukan" % data['MWSKZ']
                                    if data['poitem_del'] == 'L':
                                        po_line.write({'active': False})
                                    else:
                                        po_line.write({'product_qty': qty,'price_unit':price,'taxes_id': [(6, 0, [x.id for x in tax])]})

                                else:
                                    if data['poitem_del'] == 'L':
                                        continue
                                    else:
                                        if txt_data['po_jenis'] == 'JASA':
                                            price = float(data['po_price']) / qty
                                        else:
                                            price = float(data['po_price'])
                                        prod = self.env['product.product'].sudo().search([
                                            ('default_code', '=', data['prd_no'])], limit=1)
                                        if not prod:
                                            prod = self.env['product.product'].sudo().create({
                                                'name': data['prd_desc'],'default_code':data['prd_no']})
                                        tax = self.env['account.tax'].sudo().search([
                                            ('name', '=', data['tax_code'])], limit=1)
                                        if not tax:
                                            return "Kode Pajak  : %s tidak ditemukan" % data['MWSKZ']

                                        uom = self.env['uom.uom'].sudo().search([
                                            ('name', '=', data['po_uom'])], limit=1)
                                        if not uom:
                                            uom = self.env['uom.uom'].sudo().create({
                                                'name': data['po_uom'], 'category_id': 1})
                                        line = self.env['purchase.order.line'].sudo().create({
                                                'order_id':record.id,
                                                'sequence': int(seq),
                                                'product_id': prod.id if prod else False,
                                                'product_qty': qty,
                                                'product_uom': uom.id,
                                                'price_unit': price,
                                                'taxes_id': [(6, 0, [x.id for x in tax])]})

                                    continue

                                continue
                            record.sudo().update_gr()
                        else:
                            pass
                else:
                    pass
        except:
            pass


            #raise UserError(_("Connection Failed. Please Check Your Internet Connection."))

    def update_po(self):
        url_config = self.env['wika.integration'].search([('name', '=', 'URL PO')], limit=1)
        url = url_config.url + 'services/auth'
        url_get_po = url_config.url + 'services/getposap'
        # print (url)
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "entitas": "FMS",
            "skey": "OAZvRmB7HKDdDkKF29DXZwgSmlv9KqQWZNDWV51SACAbhnOvuA1AvZf5FnIBrLxC"
        })
        payload = payload.replace('\n', '')

        try:
            # 1. Get W-KEY TOKEN
            response = requests.request("POST", url, data=payload, headers=headers)
            w_key = (response.headers['w-key'])
            csrf = {'w-access-token': str(w_key)}
            headers.update(csrf)
            if self.level=='Proyek':
                profit_center=self.project_id.sap_code
            else:
                profit_center=self.branch_id.sap_code
            payload_2 = json.dumps({"profit_center": "%s",
                                    "po_doc": "%s",
                                    "po_jenis": "",
                                    "po_dcdat": "",
                                    "po_crdate": "%s",
                                    "po_plant": "A000",
                                    "co_code": "A000",
                                    "po_del": "",
                                    "poitem_del": "",
                                    "incmp_cat": "","po_lcdat":""
                                    }) % (profit_center, self.name,self.tgl_create_sap)
            payload_2 = payload_2.replace('\n', '')
            _logger.info(payload_2)
            response_2 = requests.request("POST", url_get_po, data=payload_2, headers=headers)
            txt = json.loads(response_2.text)
            print (txt)
            if 'data' in txt:
                if txt['data']:
                    vals = []
                    print (txt['data'])
                    txt_data = txt['data']
                    for data in txt_data['isi']:
                        seq = float(data['po_no'])
                        qty = float(data['po_qty'])
                        po_line = self.env['purchase.order.line'].sudo().search([
                            ('order_id', '=', self.id),
                            ('sequence', '=', int(seq))], limit=1)
                        print (po_line)
                        if po_line.id:
                            if txt_data['po_jenis'] == 'JASA':
                                price = float(data['po_price']) / qty
                            else:
                                price = float(data['po_price'])
                            tax = self.env['account.tax'].sudo().search([
                                ('name', '=', data['tax_code'])], limit=1)
                            if not tax:
                                return "Kode Pajak  : %s tidak ditemukan" % data['MWSKZ']
                            if data['poitem_del'] == 'L':
                                po_line.write({'active': False})
                            #
                            else:
                                po_line.write({'product_qty': qty, 'price_unit': price,
                                               'taxes_id': [(6, 0, [x.id for x in tax])]})

                        else:
                            if data['poitem_del'] == 'L':
                                continue
                            else:
                                print (data['poitem_del'])
                                if txt_data['po_jenis'] == 'JASA':
                                    price = float(data['po_price']) / qty
                                else:
                                    price = float(data['po_price'])
                                prod = self.env['product.product'].sudo().search([
                                    ('default_code', '=', data['prd_no'])], limit=1)
                                if not prod:
                                    return "Material/Service  : %s tidak ditemukan" % (data['prd_no'])
                                tax = self.env['account.tax'].sudo().search([
                                    ('name', '=', data['tax_code'])], limit=1)
                                if not tax:
                                    return "Kode Pajak  : %s tidak ditemukan" % data['MWSKZ']

                                uom = self.env['uom.uom'].sudo().search([
                                    ('name', '=', data['po_uom'])], limit=1)
                                if not uom:
                                    uom = self.env['uom.uom'].sudo().create({
                                        'name': data['po_uom'], 'category_id': 1})
                                line = self.env['purchase.order.line'].sudo().create({
                                        'order_id':self.id,
                                        'sequence': int(seq),
                                        'product_id': prod.id if prod else False,
                                        'product_qty': qty,
                                        'product_uom': uom.id,
                                        'price_unit': price,
                                        'taxes_id': [(6, 0, [x.id for x in tax])]})

                                continue
                        continue
                    #     else:
                    #         print("emang gak masuk sini 4444444444?")
                    #
                    #         vals.append((0, 0, {
                    #             'order_id': self.id,
                    #             'sequence': int(seq),
                    #             'product_id': prod.id if prod else False,
                    #             'product_qty': qty,
                    #             'product_uom': uom.id,
                    #             'price_unit': price,
                    #             'taxes_id': [(6, 0, [x.id for x in tax])]
                    #
                    #                  }))
                    #         print(vals)
                    # if vals:
                    #     print ("kkkk")
                    #     line=self.env['purchase.order.line'].sudo().create({
                    #         'order_id':self.id,
                    #         'sequence': int(seq),
                    #         'product_id': prod.id if prod else False,
                    #         'product_qty': qty,
                    #         'product_uom': uom.id,
                    #         'price_unit': price,
                    #         'taxes_id': [(6, 0, [x.id for x in tax])]})
                    #
                    #     # else:
                    #     #     po_line.create({'order_id'quantity': qty})
                    # else:
                    #     pass
            else:
                pass
        except:
            pass


            #raise UserError(_("Connection Failed. Please Check Your Internet Connection."))

    def update_gr(self):
        config = self.env['wika.integration'].search([('name', '=', 'URL GR')], limit=1)
        url_config = config.url
        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }
        for record in self:
            payload = json.dumps({
                "IV_EBELN": "%s",
                "IV_REVERSE": "",
                "IW_CPUDT_RANGE": {
                    "CPUDT_LOW": "%s",
                    "CPUTM_LOW": "00:00:00",
                    "CPUDT_HIGH": "2025-12-31",
                    "CPUTM_HIGH": "23:59:59"
                }
            }) % (record.name, record.begin_date)
            payload = payload.replace('\n', '')
            current_datetime_str = fields.Datetime.now()
            noted_message = f"updated {current_datetime_str}"
            try:
                response = requests.request("GET", url_config, data=payload, headers=headers)
                txt = json.loads(response.text)
                self.env['wika.integration.line'].sudo().create({
                    'integration_id': config.id,
                    'request_date': fields.Date.today()})
                if record.po_type != 'JASA':
                    if txt['DATA']:
                        txt_data = sorted(txt['DATA'], key=lambda x: x["MAT_DOC"])
                        mat_doc_dict = {}
                        for hasil in txt_data:
                            mat_doc = hasil["MAT_DOC"]
                            if mat_doc in mat_doc_dict:
                                # Append the item to the existing list
                                mat_doc_dict[mat_doc].append(hasil)
                            else:
                                # Create a new list with the current item
                                mat_doc_dict[mat_doc] = [hasil]
                        for mat_doc, items in mat_doc_dict.items():
                            vals = []
                            for item in items:
                                picking = self.env['stock.picking'].sudo().search([
                                    ('name', '=', item['MAT_DOC']), ('po_id', '=', record.id)], limit=1)
                                if picking.id:
                                    if item['REVERSE'] == 'X':
                                        picking.write({'active': False})
                                        move = self.env['stock.move'].sudo().search([
                                            ('sequence', '=', item['MATDOC_ITM']), ('picking_id', '=', picking.id)], limit=1)
                                        move.write({'active': False})
                                        move_line = self.env['stock.move.line'].sudo().search([
                                            ('picking_id', '=', picking.id), ('move_id', '=', move.id)], limit=1)
                                        move_line.write({'active': False})
                                    else:
                                        move = self.env['stock.move'].sudo().search([
                                            ('sequence', '=', item['MATDOC_ITM']), ('picking_id', '=', picking.id)], limit=1)
                                        if move.id:
                                            qty = float(item['QUANTITY'])
                                            state=picking.state
                                            if qty != move.product_uom_qty:
                                                move.write({'product_uom_qty': float(item['QUANTITY']), 'quantity_done': float(item['QUANTITY']),'state':state})
                                                picking.write({'note': 'updated','state':state})
                                if not picking.id:
                                    if item['REVERSE'] == '':

                                        prod = self.env['product.product'].sudo().search([
                                                    ('default_code', '=', item['MATERIAL'])], limit=1)
                                        qty = float(item['QUANTITY']) * 100
                                        uom = self.env['uom.uom'].sudo().search([
                                                    ('name', '=', item['ENTRY_UOM'])], limit=1)
                                        if not uom:
                                            uom = self.env['uom.uom'].sudo().create({
                                                'name': hasil['ENTRY_UOM'], 'category_id': 1})
                                        po_line= self.env['purchase.order.line'].sudo().search([
                                                 ('order_id', '=' ,self.id),('sequence','=',item['PO_ITEM'])] ,limit=1)
                                        vals.append((0, 0, {
                                            'sequence':item['MATDOC_ITM'],
                                            'product_id': prod.id if prod else False,
                                            'quantity_done': float(item['QUANTITY']),
                                            'product_uom_qty': float(item['QUANTITY']),
                                            'product_uom': uom.id,
                                            #'active':active,
                                            'state':'waits',
                                            'location_id': 4,
                                            'location_dest_id': 8,
                                            'purchase_line_id':po_line.id,
                                            'name': hasil['PO_NUMBER']
                                        }))
                                        docdate = hasil['DOC_DATE']
                                    if vals:
                                        picking_create = self.env['stock.picking'].sudo().create({
                                            'name': mat_doc,
                                            'po_id': record.id,
                                            'purchase_id':record.id,
                                            'project_id': record.project_id.id,
                                            'branch_id': record.branch_id.id,
                                            'department_id': record.department_id.id if record.department_id.id else False,
                                            'scheduled_date': docdate,
                                            'start_date': docdate,
                                            'partner_id': record.partner_id.id,
                                            'location_id': 4,
                                            'location_dest_id': 8,
                                            'picking_type_id': 1,
                                            'move_ids': vals,
                                            'pick_type': 'gr',
                                            #'move_ids_without_package':vals,
                                            'company_id': 1,
                                            'state': 'waits'
                                        })
                                        picking_create.write({'state': 'waits'})



                                      #raise UserError(_("Data GR Tidak Tersedia di PO TERSEBUT!"))
                    else:
                        pass

                else:
                    if txt['DATA']:
                        txt_data = sorted(txt['DATA'], key=lambda x: x["MAT_DOC"])
                        mat_doc_dict = {}
                        ses_number_dict = {}
                        for hasil in txt_data:
                            mat_doc = hasil["MAT_DOC"]
                            ses_number = hasil["SES_NUMBER"]
                            if ses_number in ses_number_dict:
                                # Append the item to the existing list
                                ses_number_dict[ses_number].append(hasil)
                            else:
                                # Create a new list with the current item
                                ses_number_dict[ses_number] = [hasil]
                        for ses_number, items in ses_number_dict.items():
                            vals = []
                            for item in items:
                                qty = float(item['QUANTITY'])
                                picking = self.env['stock.picking'].sudo().search([
                                    ('origin', '=', item['MAT_DOC']), ('name', '=', item['SES_NUMBER']),('po_id', '=', record.id)], limit=1)
                                if picking.id:
                                    if item['REVERSE'] == 'X':
                                        picking.write({'active': False})
                                        move = self.env['stock.move'].sudo().search([
                                            ('sequence', '=', item['MATDOC_ITM']), ('picking_id', '=', picking.id)],
                                            limit=1)
                                        move.write({'active': False})
                                        move_line = self.env['stock.move.line'].sudo().search([
                                            ('picking_id', '=', picking.id), ('move_id', '=', move.id)], limit=1)
                                        move_line.write({'active': False})
                                    else:
                                        move = self.env['stock.move'].sudo().search([
                                            ('sequence', '=', item['MATDOC_ITM']), ('picking_id', '=', picking.id)],
                                            limit=1)
                                        if move.id:
                                            state = picking.state
                                            if qty != move.product_uom_qty:
                                                move.write({'product_uom_qty': float(item['QUANTITY']), 'quantity_done': float(item['QUANTITY']), 'state': state})
                                                picking.write({'note': 'updated', 'state': state})

                                if not picking.id:
                                    if item['REVERSE'] == '':
                                        prod = self.env['product.product'].sudo().search([
                                            ('default_code', '=', item['MATERIAL'])], limit=1)
                                        uom = self.env['uom.uom'].sudo().search([
                                            ('name', '=', item['ENTRY_UOM'])], limit=1)
                                        if not uom:
                                            uom = self.env['uom.uom'].sudo().create({
                                                'name': hasil['ENTRY_UOM'], 'category_id': 1})
                                        po_line = self.env['purchase.order.line'].sudo().search([
                                            ('order_id', '=', self.id), ('sequence', '=', item['PO_ITEM'])], limit=1)
                                        vals.append((0, 0, {
                                            'sequence': item['MATDOC_ITM'],
                                            'product_id': prod.id if prod else False,
                                            'quantity_done': float(item['QUANTITY']),
                                            'product_uom_qty': float(item['QUANTITY']),
                                            'product_uom': uom.id,
                                            #'active': active,
                                            'state':'waits',
                                            'location_id': 4,
                                            'location_dest_id': 8,
                                            'purchase_line_id': po_line.id,
                                            'name': hasil['PO_NUMBER']
                                        }))
                                        docdate = hasil['DOC_DATE']
                                        matdoc = item['MAT_DOC']

                                    if vals:
                                        picking_create = self.env['stock.picking'].sudo().create({
                                            'name': ses_number,
                                            'po_id': record.id,
                                            'purchase_id': record.id,
                                            'project_id': record.project_id.id,
                                            'branch_id': record.branch_id.id,
                                            'department_id': record.department_id.id if record.department_id.id else False,
                                            'scheduled_date': docdate,
                                            'start_date': docdate,
                                            'partner_id': record.partner_id.id,
                                            'location_id': 4,
                                            'location_dest_id': 8,
                                            'picking_type_id': 1,
                                            'move_ids': vals,
                                            'pick_type': 'ses',
                                            'origin':matdoc,
                                            #'move_ids_without_package':vals,
                                            'company_id': 1,
                                            'state': 'waits'
                                        })
                                        picking_create.write({'state': 'waits'})
                                    else:
                                        pass
                            #raise UserError(_("Data GR Tidak Tersedia di PO TERSEBUT!"))

                    else:
                        pass

            except:
                pass