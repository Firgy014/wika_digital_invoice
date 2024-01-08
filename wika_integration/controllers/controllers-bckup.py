from odoo import http
import requests, json
from datetime import datetime
from odoo.http import request, _logger, Response


class wzoneLogin(http.Controller):

    def _login_redirect(self, uid, redirect=None):
        return redirect if redirect else '/web'

    @http.route('/auth/login/', type='http', auth='public', website=True)
    def index(self, **kw):
        ress = request.env['wika.integration'].sudo().search([('name', '=', 'Login WZONE')], limit=1)
        secret_key = ress.app_secret
        url = ress.url
        token = kw.get('token')
        request.redirect('/web/session/destroy')
        # return token
        # request.session.logout()
        res = requests.get(
            '%s?token=%s&app_secret=%s' % (url, token, secret_key))
        #     'http://localhost:8070/auth/login/test/')
        # res = requests.get('http://localhost:8070/auth/login/test/')
        data = json.loads(res.content.decode('utf-8'))
        # return res.content
        # return data["responseData"]["nip"]
        cek_user = request.env['res.users'].sudo().search([('login','=',data["responseData"]["nip"])])
        if not cek_user:
            user_vals = {
                'name': data["responseData"]["nip"],
                'login': data["responseData"]["nip"],
                'password': data["responseData"]["nip"],
                'groups_id':[(6, 0,[])]
            }
            user_id = request.env['res.users'].create(user_vals)
            groups_obj = request.env["res.groups"].sudo().search(['|',('name','=',data["responseData"]["jabatan"]),
                                                               ('name','=','LOAN')])
            if groups_obj:
                for group_obj in groups_obj:
                    group_obj.write({"users": [(4, user_id.id, 0)]})

        uid = request.session.authenticate(request.session.db, data["responseData"]["nip"], data["responseData"]["nip"])
        if uid is not False:
            request.params['login_success'] = True
            return http.redirect_with_hash(self._login_redirect(uid, redirect='/web'))
        # return  data

    @http.route('/auth/delete/', type='json', methods=['POST'], csrf=False, auth='public', website=True)
    def hapus(self, **kw):
        data = request.jsonrequest
        print('----data----',data)
        check_user = request.env['res.users'].sudo().search([('login', '=', data['nip']), ('active', '=', True)])
        if check_user:
            check_user.active = False
        return data

    @http.route('/auth/login/test/', type='http', auth='public')
    def testt(self, **kw):
        # data = {
        #       "responseStatus": 1,
        #       "responseMsg": "Success.",
        #       "responseData": {
        #         "id": "1035",
        #         "full_name": "RIHA RIZANAH",
        #         "nip": "ET133126",
        #         "email": "test@wika.co.id",
        #         "active_directory": "WIKA\\test",
        #         "username": "ET133126",
        #         "alamat": None,
        #         "lokasi": "JAKARTA",
        #         "gender": "WANITA",
        #         "religion": "Islam",
        #         "pos_code": None,
        #         "handphone": "083821348593",
        #         "tempat_lahir": "JAKARTA",
        #         "dob": "1984-10-09",
        #         "direktorat": "DIREKTORAT QUALITY, HEALTH, SAFETY AND ENVIRONTMENT",
        #         "departemen": "DEPARTEMEN PENGEMBANGAN SISTEM",
        #         "jabatan": "AHLI MADYA 2",
        #         "fungsi_bidang": "INFORMATION TECHNOLOGY",
        #         "posisi": "Ahli Madya 2 Sistem Informasi",
        #         "hak_akses": "HCIS",
        #         "status": "aktif",
        #         "kd_jabatan": "607",
        #         "kd_unit_org": "100008002001002000000000000000",
        #         "nm_unit_org": "FUNGSI KEAHLIAN SISTEM INFORMASI",
        #         "direksi": "DIREKTUR UTAMA PT WIJAYA KARYA (PERSERO) Tbk",
        #         "nm_biro": "BIRO SISTEM INFORMASI",
        #         "kd_bagian": "",
        #         "nm_bagian": None,
        #         "kd_subbagian": "",
        #         "nm_subbagian": None,
        #         "kd_fungsi_bidang": "100000",
        #         "nm_fungsi_bidang": "INFORMATION TECHNOLOGY",
        #         "kd_fungsi_bidang_lvl1": "100000",
        #         "nm_fungsi_bidang_lvl1": "INFORMATION TECHNOLOGY",
        #         "kd_fungsi_bidang_lvl2": "",
        #         "nm_fungsi_bidang_lvl2": "",
        #         "kd_fungsi_bidang_lvl3": "",
        #         "kd_kantor": "100000000000000",
        #         "nm_kantor": "Kantor Pusat",
        #         "cmp_id": "CMP-000001",
        #         "perusahaan": "PT WIJAYA KARYA (PERSERO) Tbk.",
        #         "no_sk": "SK.02.01/A.DEP.HC.14770/2016",
        #         "tgl_sk": "2016-12-05",
        #         "kd_dep": "A",
        #         "ntname": "WIKA\\riha",
        #         "no_spk": None,
        #         "nama_real": None,
        #         "nama_proyek": None,
        #         "jns_organisasi": "PUSAT",
        #         "photo": "https://new-portal.wika.co.id/assets/images/user-5ce78adb5e913.jpg"
        #       }
        # }\

        listdata = []
        data = request.env['noncash.loan'].sudo().search([], limit=10)
        for x in data:
            listdata.append({
                "id": x.id})

        data = {
            "code": 1,
            "total_seluruh_data": 45,
            "total_tampilkan_data": 45,
            "status": 200,
            "data": listdata}
        jess = json.dumps(data)

        return jess

    @http.route('/api/v1/sign-in', website=True, auth='public', methods=['POST'], csrf=False, type='json')
    def login_pajakku(self, **post):
        data = request.jsonrequest
        vals = {
            'login': 'WIKAPUSAT',
            'password': '123456',
            'rememberMe': 'true'
        }



class api(http.Controller):

    def search_data_api(self, data, table):

        if table == 'res_partner':
            nasabah = request.env['res.partner'].sudo().search(['|', ('ref', 'ilike', data),
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

        if table == 'res_branch':
            alias = request.env['res.branch'].sudo().search([('alias', 'ilike', data)], limit=1)
            return alias.id

        if table == 'res_branch object':
            alias = request.env['res.branch'].sudo().search([('alias', 'ilike', data)], limit=1)
            return alias

        if table == 'res_branch object code':
            alias = request.env['res.branch'].sudo().search([('code', '=', data)], limit=1)
            return alias

        if table == 'wika_project':
            kode_projek = request.env['wika.project'].sudo().search([
                ('code', 'ilike', data['kode_projek']), ('branch_id', '=', data['id_department'])], limit=1)
            return kode_projek

        if table == 'res_partner_bank':
            kode_bank_id = request.env['res.partner.bank'].sudo().search([('kode_bank', 'ilike', data)], limit=1)
            return kode_bank_id.id

        if table == 'res_branch':
            kode_department = request.env['res.branch'].sudo().search([('alias', 'ilike', data)], limit=1)
            return kode_department.id

        if table == 'account_move':
            jurnal = request.env['account.move'].sudo().search([('ref', 'ilike', data['nobukti']),
                                                                ('branch_id', '=', data['id_department'])], limit=1)
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

        if table == 'account_account':
            account = request.env['account.account'].sudo().search([('code', 'ilike', data['kode_perkiraan']),
                                                                    ('company_id', '=', data['company_id'])], limit=1)
            return account

        if table == 'account_tax':
            account = request.env['account.tax'].sudo().search([('account_id', '=', data)], limit=1)
            return account.id

        if table == 'loan_jenis':
            nama_jenis = request.env['loan.jenis'].sudo().search([('nama', 'ilike', data)], limit=1)
            return nama_jenis


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

    @http.route('/datanasabahmulti-api', website=True, auth='public', methods=['POST'], csrf=False, type='json')
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
                return "Kode nasabah : %s tidak ditemukan" % data['kode_partner']

        id_department = self.search_data_api(data['kode_department'], 'res_branch')
        if not id_department:
            return "Kode department : %s tidak ditemukan" % data['kode_department']

        id_department_wil = None
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
            'is_pmcs': data['is_pmcs']
        }

        spk = {
            'kode_projek': data['code'],
            'id_department': id_department
        }
        kode_spk = self.search_data_api(spk, 'wika_project')
        if kode_spk:
            # id_department = self.search_data_api(data['kode_department'], 'hr_department')
            # if not id_department:
            #     return "Kode : %s tidak ditemukan" % data['kode_department']
            kode_spk.write(vals)
        else:
            project_id=request.env['wika.project'].sudo().create(vals)
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
                'is_pmcs': data['is_pmcs']
            }

            spk = {
                'kode_projek': data['code'],
                'id_department': id_department
            }
            kode_spk = self.search_data_api(spk, 'wika_project')
            if kode_spk:
                # id_department = self.search_data_api(data['kode_department'], 'hr_department')
                # if not id_department:
                #     return "Kode : %s tidak ditemukan" % data['kode_department']
                kode_spk.write(vals)
            else:
                project_id = request.env['wika.project'].sudo().create(vals)
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

    @http.route('/datajurnal-api', website=True, auth='public', methods=['POST'], csrf=False, type='json')
    def datajurnal(self, **kw):
        data_array = request.jsonrequest
        # _logger.info(data_array['result'])

        for data in data_array['result']:
            # cari id department (branch) - solved
            id_department = self.search_data_api(data['kddivisi'], 'res_branch')
            if not id_department:
                return "Kode department : %s tidak ditemukan" % data['kddivisi']

            # cari nomor bukti ini sudah ada atau belum - solved
            jurnal = {
                'nobukti': data['nobukti'],
                'id_department': id_department
            }
            cek_move = self.search_data_api(jurnal, 'account_move')
            id_move = None
            amount = None
            journal_id = None
            if cek_move:
                id_move = cek_move.id
                amount = cek_move.amount
                journal_id = cek_move.journal_id

            # cari kode perkiraan - solved
            kode_perkiraan = self.search_data_api(data['kdperkiraan'], 'account_account')
            if not kode_perkiraan:
                return "Kode perkiraan : %s tidak ditemukan" % data['kdperkiraan']
            else:
                id_coa = kode_perkiraan.id
                id_utype = kode_perkiraan.user_type_id.id

            # cari no bukti pelunasan - solved
            if len(data['buktipelunasan']) > 0:
                jurnal = {
                    'nobukti': data['buktipelunasan'],
                    'id_department': id_department,
                    'acc_id': id_coa,
                    'project_code': data['kdspk']
                }
                bukti_pelunasan = self.search_data_api(jurnal, 'account_move_line')
                if not bukti_pelunasan:
                    return "No bukti pelunasan : %s " \
                           "di departemen %s dengan kode spk " \
                           "%s dan kode perkiraan " \
                           "%s, tidak ditemukan" % (data['buktipelunasan'], data['kddivisi'],
                                                    data['kdspk'], data['kdperkiraan'])
            # cari kode partner - solved
            id_partner = None
            if len(data['kdnasabah']) > 0:
                kode_partner = self.search_data_api(data['kdnasabah'], 'res_partner')
                if id_utype in (1, 2):
                    if not kode_partner:
                        return "Kode nasabah %s tidak ditemukan" % data['kdnasabah']
                    else:
                        id_partner = kode_partner.id

            statusjid = 0
            statusupdate = 0
            statusmove = 0
            id_jid = 0
            date_write = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rupiah = float(data['rupiah'])
            if not id_move:
                # jika tidak ada, create account move baru. Jurnal id sementara misc dulu = 3.
                if data['dk'] == 'D':
                    amount_awal = float(rupiah)
                else:
                    amount_awal = 0

                vals = {
                    'date': data['tanggal'],
                    'journal_id': 3,
                    'state': 'posted',
                    'branch_id': id_department,
                    'ref': data['nobukti'],
                    'name': data['nobukti'],
                    'amount': amount_awal,
                    'currency_id': 13,
                    'partner_id': id_partner,
                    'company_id': 1,
                    'create_uid': 1,
                    'create_date': date_write,
                    'write_uid': 1,
                    'write_date': date_write
                }
                acc_move = request.env['account.move'].sudo().create(vals)
                statusmove = 1
                id_move = acc_move.id
                amount = acc_move.amount
                journal_id = acc_move.journal_id
            else:
                # jika ada, update amount account move
                # cari jid yang diinput sudah ada atau belum sesuai dengan department
                vjid = {
                    'jid': data['jid'],
                    'id_department': id_department
                }
                jurnal_jid = self.search_data_api(vjid, 'account_move_line_jid')
                # jika jid tidak ada, maka move ditambah amount nya dan jid ini diinsert ke move line. Jika ada di cek dulu
                # ketika date_writenya beda baru direplace.
                if jurnal_jid:
                    if jurnal_jid.write_date == data['date_modif']:
                        statusjid = 1
                    else:
                        amount -= jurnal_jid.debit
                        if data['dk'] == 'D':
                            amount += rupiah
                        id_jid = jurnal_jid
                        statusupdate = 1
                else:
                    if data['dk'] == 'D':
                        amount += rupiah

            # cek date modified
            if len(data['date_modif']) > 0:
                date_write = data['date_modif']

            if statusjid == 0:
                id_projek = None
                # cek SPK
                if len(data['kdspk']) > 0:
                    vproj = {
                        'kode_department': data['kdspk'],
                        'id_department': id_department,
                    }
                    projek = self.search_data_api(vproj, 'wika_project')
                    if not projek:
                        return "Kode SPK %s di departemen %s tidak ditemukan" % (data['kdspk'], data['kddivisi'])
                    else:
                        id_projek = projek.id
                # cek tax id
                tax = self.search_data_api(id_coa, 'account_tax')
                if tax:
                    id_tax = tax

                # definisi nilai debit, kredit, residual, id_jurnal
                debit = 0
                kredit = 0
                balance = 0
                amount_residual = 0
                id_jurnal = 0
                if data['dk'] == 'D':
                    debit = rupiah
                    balance = rupiah
                    if id_utype == 1:
                        amount_residual = debit
                        id_jurnal = 1
                else:
                    kredit = rupiah
                    balance = 0 - rupiah
                    if id_utype == 2:
                        amount_residual = 0 - kredit
                        id_jurnal = 2

                # //cek id jurnal sekarang apakah termasuk jurnal receivable, payable, atau masih misc.
                if id_jurnal != 0:
                    journal_id = id_jurnal
                    valupdate = {
                        'journal_id': journal_id
                    }
                    id_move.write(valupdate)

                vals = {
                    'move_id': id_move,
                    'account_id': id_coa,
                    'branch_id': id_department,
                    'partner_id': id_partner,
                    'sumberdaya': data['kdsbdaya'],
                    'alat': data['kdalat'],
                    'tahap': data['kdtahap'],
                    'depart_id': id_department,
                    'name': data['keterangan'],
                    'quantity': data['volume'],
                    'debit': debit,
                    'credit': kredit,
                    'project_code': data['kdspk'],
                    'faktur_pajak': data['faktur_pajak'],
                    'no_kontrak': data['nokontrak'],
                    'date_maturity': data['tanggal'],
                    'date': data['tanggal'],
                    'balance': balance,
                    'debit_cash_basis': 0,
                    'credit_cash_basis': 0,
                    'balance_cash_basis': 0,
                    'amount_currency': 0,
                    'company_currency_id': 13,
                    'currency_id': 13,
                    'amount_residual': amount_residual,
                    'amount_residual_currency': 0,
                    'tax_base_amount': 0,
                    'ref': data['nobukti'],
                    'reconciled': 'f',
                    'blocked': 'f',
                    'company_id': 1,
                    'tax_exigible': 't',
                    'create_uid': 1,
                    'create_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'write_uid': 1,
                    'write_date': date_write,
                    'jid': data['jid'],
                    'no_bukti_penerbitan': data['buktipelunasan'],
                    'projek_id': id_projek,
                    'internal_note': 'Via API'
                }
                if statusupdate == 0:
                    moveline = request.env['account.move.line'].sudo().create(vals)
                else:
                    id_jid.write(vals)

                if statusmove == 0:
                    vals = {
                        'amount': amount
                    }
                    id_move.write(vals)

            if bukti_pelunasan:
                amount_res = 0
                amount_rupiah = 0
                if data['dk'] == 'D':
                    amount_rupiah = rupiah

                if amount_rupiah != 0:
                    amount_res = bukti_pelunasan.amount_residual
                    if amount_res < 0:
                        camount = amount_res + amount_rupiah
                    elif amount_res > 0:
                        camount = amount_res + amount_rupiah
                    vals = {
                        'amount_residual': camount
                    }
                    bukti_pelunasan.write(vals)

    @http.route('/api/ncl_pembukaan', website=True, auth='public', methods=['POST'], csrf=False, type='json')
    def ncl_pembukaan(self,**kw):
        data_array = request.jsonrequest
        _logger.info(data_array['result'])
        # return data_array['result']

        for data in data_array['result']:
            nasabah_tipe = data['nasabah_tipe'].split()
            if nasabah_tipe[0] == 'SKBDN':
                tipe = 'SKBDN/LC'
                jenis = nasabah_tipe[1]

            else:
                tipe = 'SCF'
                jenis = nasabah_tipe[0]

            if jenis == 'SUBKON':
                jenis = 'SUBKONT'

            jenis_id = self.search_data_api(tipe, 'loan_jenis')

            nasabah = self.search_data_api(data['nasabah'], 'res_partner')

            id_department = self.search_data_api(data['kddivisi'], 'res_branch')
            if not id_department:
                return "Kode department : %s tidak ditemukan" % data['kddivisi']

            id_projek = None
            # cek SPK
            if len(data['kdspk']) > 0:
                vproj = {
                    'kode_projek': data['kdspk'],
                    'id_department': id_department,
                }
                projek = self.search_data_api(vproj, 'wika_project')
                if not projek:
                    return "Kode SPK %s di departemen %s tidak ditemukan" % (data['kdspk'], data['kddivisi'])
                else:
                    id_projek = projek.id

            stage= request.env['loan.stage'].sudo().search([('name','=','Pengajuan'),('tipe','=','Non Cash')])

            vals = {
                "jenis_nasabah": jenis,
                "vendor_id": nasabah.id,
                "branch_id": id_department,
                "projek_id": id_projek,
                "jenis_id": jenis_id.id,
                "nama_jenis": tipe,
                "nomor_bukti": data['nobukti'],
                "tanggal_kontrak": data['tgl_kontrak'],
                "nomor_kontrak": data['no_kontrak'],
                "nilai_pokok_tagihan": data['nilai_pokok'],
                "stage_id": stage.id,
                "tgl_mulai_perkiraan": '2019-12-22',
                "tgl_akhir_perkiraan": '2019-12-23',
                "ppn": data['ppn'],
                "nilai_pokok_ppn": data['pokok_ppn'],
                "potongan_pph": data['potong_pph'],
                "potongan_lain": data['potong_lain'],
                "nilai_tagihan_netto": data['tagihan_netto'],
                "jumlah_pengajuan": data['pembayaran'],
                "is_pmcs": True
            }
            generate = request.env['noncash.loan'].sudo().create(vals)
        # return generate


    @http.route('/datajurnal-delete', website=True, auth='public', methods=['POST'], csrf=False, type='json')
    def jurnal_cancel(self,**kw):
        data_array = request.jsonrequest
        for data in data_array['result']:
            id_department = self.search_data_api(data['kddivisi'], 'res_branch object')
            if not id_department:
                return "Kode department : %s tidak ditemukan" % data['kddivisi']

            jurnal = {
                'nobukti': data['no_bukti'],
                'id_department': id_department.id
            }
            cek_move = self.search_data_api(jurnal, 'account_move')
            if cek_move:
                if cek_move.state=='posted':
                    cek_move.button_cancel()


    @http.route('/datajurnal-anak-api', website=True, auth='public', methods=['POST'], csrf=False, type='json')
    def datajurnalanak(self, **kw):
        data_array = request.jsonrequest
        _logger.info("Data Result ===== %r",data_array['result'])
        i=0
        lvals=[]
        aml_obj = request.env['account.move.line'].sudo().with_context(check_move_validity=False)
        nobukti=''
        move = None
        for data in data_array['result']:

            _logger.info("masuk ke for ------- %r",data)

            # Cari ID Department
            id_department = self.search_data_api(data['kode_divisi'], 'res_branch object code')
            if not id_department:
                return "Kode department : %s tidak ditemukan" % data['kode_divisi']
            _logger.info("masuk ke data dept ------- %r", id_department)

            if i==0:
                tanggal = datetime.strptime(data['tanggal'], "%Y-%m-%d")
                yeartanggal = tanggal.year
                yearnext = tanggal.year
                monthtanggal = tanggal.month
                monthnext = tanggal.month + 1
                if monthnext > 12:
                    monthnext -= 1
                    yearnext = yeartanggal + 1
                tanggaltanggal = "%s-%s-01" % (yeartanggal, monthtanggal)
                tanggalnext = "%s-%s-01" % (yearnext, monthnext)
                moves = request.env['account.move'].sudo().search([('branch_id','=',id_department.id),
                                                                   ('date','>=',tanggaltanggal),
                                                                   ('date','<',tanggalnext)])
                for mv in moves:
                    mv.sudo().unlink()

                nobukti=data['no_bukti']
                i+=1

            if nobukti!=data['no_bukti']:
                # mvl = request.env['account.move.line'].sudo().search([('move_id', '=', move.id)])
                # if move.state == 'posted':
                #     move.button_cancel()
                move.line_ids.unlink()
                print(lvals)
                _logger.info("masuk ke lvals ------- %r",lvals)
                for x in lvals:
                    aml_obj.create({
                        'name': x['name'],
                        'no_bukti_penerbitan': x['no_bukti_penerbitan'],
                        'faktur_pajak': x['faktur_pajak'],
                        'nasabah_code': x['nasabah_code'],
                        'project_code': x['project_code'],
                        'currency_id': x['currency_id'],  # default IDR
                        'credit': x['credit'],
                        'debit': x['debit'],
                        'partner_id': x['partner_id'],
                        'analytic_account_id': x['analytic_account_id'],
                        'projek_id': x['projek_id'],
                        'ref': x['ref'],
                        'move_id': x['move_id'],
                        'account_id': x['account_id'],
                        'branch_id': x['branch_id'],
                        'alat': x['alat'],
                    })
                # move.post()
                nobukti = data['no_bukti']
                lvals=[]


            # Cari ID COA yang company id nya sesuai dengan dept
            coa = {
                'kode_perkiraan': data['kode_perkiraan'],
                'company_id': id_department.company_id.id
            }
            kode_perkiraan = self.search_data_api(coa, 'account_account')
            if not kode_perkiraan:
                return "Kode perkiraan : %s tidak ditemukan" % data['kode_perkiraan']
            else:
                id_coa = kode_perkiraan.id
                id_utype = kode_perkiraan.user_type_id.id
            _logger.info("masuk ke data coa ------- %r", kode_perkiraan)
            # Cari id nasabah
            id_partner = None
            partner_dept = None
            if data['kode_nasabah']:
                if len(data['kode_nasabah']) > 0:
                    kode_partner = self.search_data_api(data['kode_nasabah'], 'res_partner')
                    if kode_partner:
                        id_partner = kode_partner.id
                        # cari department sesuai dengan nasabahnya untuk cari kode spk
                        partner_dept = self.search_data_api(kode_partner.mobile, 'res_branch')
                    else:
                        if id_utype in (1, 2):
                            if not kode_partner:
                                return "Kode nasabah %s tidak ditemukan" % data['kode_nasabah']
            _logger.info("masuk ke data partner ------- %r", id_partner)
            _logger.info("masuk ke data partner_dept ------- %r", partner_dept)
            id_projek = None
            analytic_id = None
            if data['kode_spk']:
                if len(data['kode_spk']) > 0:
                    vproj = {
                        'kode_projek': data['kode_spk'],
                        'id_department': partner_dept,
                    }
                    projek = self.search_data_api(vproj, 'wika_project')
                    if not projek:
                        return "Kode SPK %s di departemen %s (nasabah %s) tidak ditemukan" % (data['kode_spk'],partner_dept, data['kode_nasabah'])
                    else:
                        id_projek = projek.id
                        analytic_id=None
                        if projek.analytic_account_id:
                            analytic_id = projek.analytic_account_id.id

            _logger.info("masuk ke data project ------- %r", id_projek)
            jurnal = {
                'nobukti': nobukti,
                'id_department': id_department.id
            }
            cek_move = self.search_data_api(jurnal, 'account_move')
            journal = {
                'code': id_department.code,
                'company_id': id_department.company_id.id
            }
            id_journal = self.search_data_api(journal, 'account_journal name')
            if cek_move:
                move=cek_move
            else:
                mvals = {
                    'date': data['tanggal'],
                    'journal_id': id_journal,
                    'ref': nobukti,
                    'name': nobukti,
                    'partner_id': id_partner,
                    'company_id': id_department.company_id.id,
                    'branch_id': id_department.id,
                }
                move = request.env['account.move'].sudo().create(mvals)

            debit=0
            credit=0
            if data['dk']=='D':
                debit=data['rupiah']
            else:
                credit=data['rupiah']

            faktur_pajak = None
            if data['faktur_pajak']:
                if len(data['faktur_pajak']) > 0:
                    faktur_pajak = data['faktur_pajak']

            no_bukti_terbit = None
            if data['no_bukti_terbit']:
                if len(data['no_bukti_terbit']) > 0:
                    no_bukti_terbit = data['no_bukti_terbit']

            kode_perkiraan_lama = None
            if data['kode_perkiraan_lama']:
                kode_perkiraan_lama = data['kode_perkiraan_lama']

            lvals.append( {
                'name': data['keterangan'],
                'no_bukti_penerbitan': no_bukti_terbit,
                'faktur_pajak': faktur_pajak,
                'nasabah_code': data['kode_nasabah'],
                'project_code': data['kode_spk'],
                'currency_id': 13,  # default IDR
                'credit': credit,
                'debit': debit,
                'amount_residual': 0,
                'partner_id': id_partner,
                'projek_id': id_projek,
                'analytic_account_id': analytic_id,
                'ref': nobukti,
                'move_id': move.id,
                'account_id': id_coa,
                'branch_id': id_department.id,
                'alat': kode_perkiraan_lama,
            })
        # if move.state=='posted':
        #     move.button_cancel()
        move.line_ids.unlink()

        _logger.info("masuk ke lvals2 ------- %r", lvals)
        leng = len(lvals)
        i = 1
        for x in lvals:
            _logger.info("------- data ke %r dari %r", i,leng)
            i += 1
            aml_obj.create({
                'name': x['name'],
                'no_bukti_penerbitan': x['no_bukti_penerbitan'],
                'faktur_pajak': x['faktur_pajak'],
                'nasabah_code': x['nasabah_code'],
                'project_code': x['project_code'],
                'currency_id': x['currency_id'],  # default IDR
                'credit': x['credit'],
                'debit': x['debit'],
                'partner_id': x['partner_id'],
                'analytic_account_id': x['analytic_account_id'],
                'projek_id': x['projek_id'],
                'ref': x['ref'],
                'move_id': x['move_id'],
                'account_id': x['account_id'],
                'branch_id': x['branch_id'],
                'alat': x['alat'],
            })
        # move.post()

        return Response("OK", status=200)

