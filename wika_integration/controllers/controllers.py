from odoo import http
import requests, json
from datetime import datetime
from odoo.http import request, _logger, Response
# from odoo.tools.translate import _
from werkzeug.utils import redirect

class wzoneLogin(http.Controller):
    
    @http.route('/auth/login/', type='http', auth='public', website=True)
    def index(self, **kw):
        # Ambil data dari sistem WZONE
        ress = request.env['wika.integration'].sudo().search([('name', '=', 'Login WZONE')], limit=1)
        token = kw.get('token')
        secret_key = ress.app_secret
        url = ress.url
        res = requests.get('%s?token=%s&app_secret=%s' % (url, token, secret_key), verify=False)
        data = json.loads(res.content.decode('utf-8'))
        request.redirect('/web/session/destroy')
        
        nip = data.get("responseData", {}).get("nip")
        
        user_exists = request.env['res.users'].sudo().search([('login','=',data["responseData"]["nip"])])
        if user_exists:
            request.session.authenticate('di_dev_2', login=nip, password= nip)
            return redirect('/web')
        else:
            return "USER/NIP anda tidak terdaftar di WDIGI, Silahkan hubungi Administrator"
            
    @http.route('/auth/delete/', type='json', methods=['POST'], csrf=False, auth='public', website=True)
    def hapus(self, **kw):
        data = request.jsonrequest
        print('----data----',data)
        check_user = request.env['res.users'].sudo().search([('login', '=', data['nip']), ('active', '=', True)])
        if check_user:
            check_user.active = False
        return data

class api(http.Controller):

    def search_data_api(self, data, table):

        if table == 'res_partner':
            nasabah = request.env['res.partner'].with_context(active_test=False).sudo().search(['|', ('ref', 'ilike', data),
                                                                ('kode_nasabah_baru', 'ilike', data)], limit=1)
            return nasabah

        if table == 'res_partner_category':
            categ = request.env['res.partner.category'].sudo().search([('name', 'ilike', data)], limit=1)
            return categ.id

        if table == 'account_journal':
            journal = request.env['account.journal'].sudo().search([('code', 'ilike', data['code']),
                                                                    ('company_id', '=', data['company_id'])], limit=1)
            return journal.id

        if table == 'account_journal name':
            journal = request.env['account.journal'].sudo().search([('name', 'ilike', data['code']),
                                                                    ('company_id', '=', data['company_id'])], limit=1)
            return journal.id

        if table == 'ir_model':
            name_model = request.env['ir.model'].sudo().search([('name', 'ilike', data)], limit=1)
            return name_model.id

        if table == 'res_users':
            kode_partner = request.env['res.users'].sudo().search([('partner_id', 'ilike', data)], limit=1)
            return kode_partner.id

        if table == 'hr_department':
            alias = request.env['hr.department'].sudo().search([('alias', 'ilike', data)], limit=1)
            return alias.id



        if table == 'res_branch object code':
            alias = request.env['res.branch'].with_context(active_test=False).sudo().search([('code', '=', data),('code', '=', data)], limit=1)

            return alias

        if table == 'project_project':
            kode_projek = request.env['project.project'].sudo().search([
                ('code', 'ilike', data['kode_projek']), ('branch_id', '=', data['id_department'])], limit=1)

            return kode_projek


        if table == 'res_partner_bank':
            kode_bank_id = request.env['res.partner.bank'].sudo().search([('kode_bank', 'ilike', data)], limit=1)
            return kode_bank_id.id

        if table == 'res_branch':
            kode_department = request.env['res.branch'].with_context(active_test=False).sudo().search([('alias', 'ilike', data)], limit=1)
            return kode_department.id

        if table == 'account_move':
            jurnal = request.env['account.move'].sudo().search([('ref', 'ilike', data['nobukti']),
                                                                ('branch_id', '=', data['id_department'])], limit=1)
            _logger.info("JURNALLLLLLLLLLLLLLLLLL %r", jurnal)
            return jurnal

        if table == 'account_move_line':
            jurnal = request.env['account.move.line'].sudo().search([('ref', 'ilike', data['nobukti']),
                                                                     ('branch_id', '=', data['id_department']),
                                                                     ('account_id', '=', data['acc_id']),
                                                                     ('project_code', '=', data['project_code'])],
                                                                    limit=1)
            return jurnal
        if table == 'account_move_line_jid':
            jurnal = request.env['account.move.line'].sudo().search([('jid', '=', data['jid']),
                                                                     ('branch_id', '=', data['id_department'])],
                                                                    limit=1)
            return jurnal


        if table == 'account_tax':
            account = request.env['account.tax'].sudo().search([('account_id', '=', data)], limit=1)
            return account.id




    @http.route('/datanasabahsingle-api', website=True, auth='public', methods=['POST'], csrf=False, type='json')
    def datanasabahsingle(self, **kw):
        data = request.jsonrequest

        kode_nasabah = self.search_data_api(data['ref'], 'res_partner')

        categ = self.search_data_api(data['categ_ids'], 'res_partner_category')

        vals = {
            'id_nasabah': data['id_nasabah'],
            'name': data['name'],
            'company_id': '1',
            'display_name': data['name'],
            'ref': data['ref'],
            'kode_nasabah_baru': data['kode_nasabah_8'],
            'lang': 'en_US',
            'vat': data['vat'],
            'website': data['website'],
            'comment': "Via API",
            'active': 't',
            'customer': 'f',
            'supplier': 't',
            'employee': 'f',
            'type': 'contact',
            'street': data['street'],
            'zip': data['zip'],
            'city': data['city'],
            # 'state_id'          : state_id,
            'country_id': '100',
            'email': data['email'],
            'phone': data['phone'],
            'is_company': 'f',
            'color': '0',
            'partner_share': 't',
            'create_uid': '1',
            'create_date': datetime.today(),
            'write_uid': '1',
            'write_date': datetime.today(),
            'message_bounce': '0',
            'invoice_warn': 'no-message',
            'sale_warn': 'no-message',
            'sap_code': data['sap_code'],
            # 'tipe_faktur'       : data['tipe_faktur'],
            # 'name_cp'           : data['name_cp'],
            # 'function_cp'       : data['function_cp'],
            # 'email_cp'          : data['email_cp'],
            # 'phone_cp'          : data['phone_cp'],
            # 'mobile_cp'         : data['mobile_cp'],
            # 'nama_bank'         : data['nama_bank'],
            # 'cabang'            : data['cabang'],
            # 'nomor_rekening'    : data['nomor_rekening'],
            # 'atas_nama'         : data['atas_nama'],
            'cotid': data['cotid'],
            'category_id': [(6, 0, {categ})]
        }
        if kode_nasabah:
            kode_nasabah.write(vals)
        else:
            request.env['res.partner'].sudo().create(vals)

    @http.route('/datanasabahmulti-api', website=True,  auth='public', methods=['POST'], csrf=False, type='json')
    def datanasabahmulti(self, **kw):
        data_array = request.jsonrequest

        for data in data_array['result']:
            kode_nasabah = self.search_data_api(data['ref'], 'res_partner')

            if data['categ_ids']:
                categ = self.search_data_api(data['categ_ids'], 'res_partner_category')
            else:
                categ = self.search_data_api("", 'res_partner_category')


            vals = {
                'id_nasabah': data['id_nasabah'],
                'name': data['name'],
                'company_id': '1',
                'display_name': data['name'],
                'ref': data['ref'],
                'kode_nasabah_baru': data['kode_nasabah_8'],
                'lang': 'en_US',
                'vat': data['vat'],
                'website': data['website'],
                'comment': "Via API",
                'active': 't',
                'customer': 'f',
                'supplier': 't',
                'employee': 'f',
                'type': 'contact',
                'street': data['street'],
                'zip': data['zip'],
                'city': data['city'],
                # 'state_id'          : state_id,
                'country_id': '100',
                'email': data['email'],
                'phone': data['phone'],
                'is_company': 'f',
                'color': '0',
                'partner_share': 't',
                'create_uid': '1',
                'create_date': datetime.today(),
                'write_uid': '1',
                'write_date': datetime.today(),
                'message_bounce': '0',
                'invoice_warn': 'no-message',
                'sale_warn': 'no-message',
                'sap_code': data['sap_code'],
                # 'tipe_faktur'       : data['tipe_faktur'],
                # 'name_cp'           : data['name_cp'],
                # 'function_cp'       : data['function_cp'],
                # 'email_cp'          : data['email_cp'],
                # 'phone_cp'          : data['phone_cp'],
                # 'mobile_cp'         : data['mobile_cp'],
                # 'nama_bank'         : data['nama_bank'],
                # 'cabang'            : data['cabang'],
                # 'nomor_rekening'    : data['nomor_rekening'],
                # 'atas_nama'         : data['atas_nama'],
                'cotid': data['cotid'],
                'category_id': [(6, 0, {categ})]
            }
            if kode_nasabah:
                kode_nasabah.write(vals)
            else:
                request.env['res.partner'].sudo().create(vals)

    @http.route('/dataprojectsingle-api', website=True, auth='public', methods=['POST'], csrf=False, type='json')
    def dataprojectsingle(self, **kw):
        data = request.jsonrequest

        partner_id = None
        if len(data['kode_partner']) > 0:
            nasabah = self.search_data_api(data['kode_partner'], 'res_partner')
            if nasabah.id:
                partner_id = nasabah.id
            else:
                return "Kode nasabah :: %s tidak ditemukan" % data['kode_partner']

        id_department = self.search_data_api(data['kode_department'], 'res_branch')
        if not id_department:
            return "Kode department : %s tidak ditemukan" % data['kode_department']

        id_department_wil = None
        if len(data['kode_wilayah']) > 0:
            wilayah = {
                'kode_projek': data['kode_wilayah'],
                'id_department': id_department
            }
            kode_wilayah = self.search_data_api(wilayah, 'project_project')
            if kode_wilayah.id:
                id_department_wil = kode_wilayah.id
            else:
                return "Kode wilayah : %s tidak ditemukan" % data['kode_wilayah']

        kode_bank = self.search_data_api(data['kode_bank'], 'res_partner_bank')
        if kode_bank == False:
            return "Kode bank : %s tidak ditemukan" % data['kode_bank']

        # model_id = self.search_data_api(data['name'], 'ir_model')
        # partner = self.search_data_api(data['partner_id'], 'res_users')

        vals = {
            'id_spk': data['id_spk'],
            'code': data['code'],
            'name': data['name'],
            'branch_id': id_department,
            'customer_id': partner_id,
            'manager': data['manager'],
            'tender': data['tender'],
            'is_jo': data['is_jo'],
            'lokasi': data['lokasi'],
            'tgl_mulai': data['tgl_mulai'],
            'tgl_selesai': data['tgl_selesai'],
            'omset': data['omset'],
            'kode_jurnal': data['kode_jurnal'],
            'bank_partner_id': kode_bank,
            'manager_kasie_keu': data['manager_kasie_keu'],
            'manager_kasie_kom': data['manager_kasie_kom'],
            'manager_kasie_dan': data['manager_kasie_dan'],
            'staff_keu': data['staff_keu'],
            'staff_kom': data['staff_kom'],
            'staff_dan': data['staff_dan'],
            'isdivisi': data['isdivisi'],
            'kode_wilayah': id_department_wil,
            'is_pmcs': data['is_pmcs'],
            'sap_code': data['sap_code'],
        }

        spk = {
            'kode_projek': data['code'],
            'id_department': id_department
        }
        kode_spk = self.search_data_api(spk, 'project_project')
        if kode_spk:
            # id_department = self.search_data_api(data['kode_department'], 'hr_department')
            # if not id_department:
            #     return "Kode : %s tidak ditemukan" % data['kode_department']
            kode_spk.write(vals)
        else:
            project_id=request.env['project.project'].sudo().create(vals)
            analytic_id=request.env['account.analytic.account'].sudo().create({
                'name': data['name'],
                'active': True,
                'code': data['code'],
                'id_projek': project_id.id,
                'company_id': '1',
                'partner_id': partner_id,
            })
            project_id.write({
                'analytic_account_id': analytic_id.id
            })

    @http.route('/dataprojectmulti-api', website=True, auth='public', methods=['POST'], csrf=False, type='json')
    def dataprojectmulti(self, **kw):
        data_array = request.jsonrequest

        for data in data_array['result']:
            partner_id = None
            if data['kode_partner']:
                if len(data['kode_partner']) > 0:
                    nasabah = self.search_data_api(data['kode_partner'], 'res_partner')
                    if nasabah.id:
                        partner_id = nasabah.id
                    else:
                        return "Kode nasabah : %s tidak ditemukan" % data['kode_partner']

            id_department = self.search_data_api(data['kode_department'], 'res_branch')
            if not id_department:
                return "Kode department : %s tidak ditemukan" % data['kode_department']

            id_department_wil = None
            if data['kode_wilayah']:
                if len(data['kode_wilayah']) > 0:
                    wilayah = {
                        'kode_projek': data['kode_wilayah'],
                        'id_department': id_department
                    }
                    kode_wilayah = self.search_data_api(wilayah, 'wika_project')
                    if kode_wilayah.id:
                        id_department_wil = kode_wilayah.id
                    else:
                        return "Kode wilayah : %s tidak ditemukan" % data['kode_wilayah']

            kode_bank = self.search_data_api(data['kode_bank'], 'res_partner_bank')
            if kode_bank == False:
                return "Kode bank : %s tidak ditemukan" % data['kode_bank']

            # model_id = self.search_data_api(data['name'], 'ir_model')
            # partner = self.search_data_api(data['partner_id'], 'res_users')

            vals = {
                'id_spk': data['id_spk'],
                'code': data['code'],
                'name': data['name'],
                'branch_id': id_department,
                'customer_id': partner_id,
                'manager': data['manager'],
                'tender': data['tender'],
                'is_jo': data['is_jo'],
                'lokasi': data['lokasi'],
                'tgl_mulai': data['tgl_mulai'],
                'tgl_selesai': data['tgl_selesai'],
                'omset': data['omset'],
                'kode_jurnal': data['kode_jurnal'],
                'bank_partner_id': kode_bank,
                'manager_kasie_keu': data['manager_kasie_keu'],
                'manager_kasie_kom': data['manager_kasie_kom'],
                'manager_kasie_dan': data['manager_kasie_dan'],
                'staff_keu': data['staff_keu'],
                'staff_kom': data['staff_kom'],
                'staff_dan': data['staff_dan'],
                'isdivisi': data['isdivisi'],
                'kode_wilayah': id_department_wil,
                'is_pmcs': data['is_pmcs'],
                'sap_code': data['sap_code'],
            }

            spk = {
                'kode_projek': data['code'],
                'id_department': id_department
            }
            kode_spk = self.search_data_api(spk, 'project_project')
            if kode_spk:
                # id_department = self.search_data_api(data['kode_department'], 'hr_department')
                # if not id_department:
                #     return "Kode : %s tidak ditemukan" % data['kode_department']
                kode_spk.write(vals)
            else:
                project_id = request.env['project.project'].sudo().create(vals)
                analytic_id = request.env['account.analytic.account'].sudo().create({
                        'name' : data['name'],
                        'active' : True,
                        'code' : data['code'],
                        'id_projek' : project_id.id,
                        'company_id' : '1',
                        'partner_id' : partner_id,
                })
                project_id.write({
                    'analytic_account_id':analytic_id.id
                })



