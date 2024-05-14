
from odoo import http
import werkzeug
from requests import Request,Session
import requests
from odoo.http import Response
import json

from odoo.http import request


class wzoneLogin(http.Controller):

    def _login_redirect(self, uid, redirect=None):
        return redirect if redirect else '/web'

    @http.route('/auth/login/', type='http', auth='public', website=True)
    def index(self, **kw):
        secret_key="92d54c383e29fed5f96654f9f00f3691"
        token =kw.get('token')
        request.redirect('/web/session/logout')
        # return token
        # request.session.logout()
        res =  requests.get(
            'https://new-portal.wika.co.id/app/sso/valid?token=%s&app_secret=%s' % (token, secret_key))
        #     'http://localhost:8070/auth/login/test/')
        # res = requests.get('http://localhost:8070/auth/login/test/')
        data=json.loads(res.content.decode('utf-8'))
        # return request.session.db
        uid = request.session.authenticate(request.session.db, data["responseData"]["nip"], data["responseData"]["nip"])
        if uid is not False:
            request.params['login_success'] = True
            return http.redirect_with_hash(self._login_redirect(uid, redirect='/web'))
        # return  data


    @http.route('/auth/login/test/', type='http', auth='public')
    def testt(self,**kw):
        data = {
              "responseStatus": 1,
              "responseMsg": "Success.",
              "responseData": {
                "id": "1035",
                "full_name": "RIHA RIZANAH",
                "nip": "ET133126",
                "email": "test@wika.co.id",
                "active_directory": "WIKA\\test",
                "username": "ET133126",
                "alamat": None,
                "lokasi": "JAKARTA",
                "gender": "WANITA",
                "religion": "Islam",
                "pos_code": None,
                "handphone": "083821348593",
                "tempat_lahir": "JAKARTA",
                "dob": "1984-10-09",
                "direktorat": "DIREKTORAT QUALITY, HEALTH, SAFETY AND ENVIRONTMENT",
                "departemen": "DEPARTEMEN PENGEMBANGAN SISTEM",
                "jabatan": "AHLI MADYA 2",
                "fungsi_bidang": "INFORMATION TECHNOLOGY",
                "posisi": "Ahli Madya 2 Sistem Informasi",
                "hak_akses": "HCIS",
                "status": "aktif",
                "kd_jabatan": "607",
                "kd_unit_org": "100008002001002000000000000000",
                "nm_unit_org": "FUNGSI KEAHLIAN SISTEM INFORMASI",
                "direksi": "DIREKTUR UTAMA PT WIJAYA KARYA (PERSERO) Tbk",
                "nm_biro": "BIRO SISTEM INFORMASI",
                "kd_bagian": "",
                "nm_bagian": None,
                "kd_subbagian": "",
                "nm_subbagian": None,
                "kd_fungsi_bidang": "100000",
                "nm_fungsi_bidang": "INFORMATION TECHNOLOGY",
                "kd_fungsi_bidang_lvl1": "100000",
                "nm_fungsi_bidang_lvl1": "INFORMATION TECHNOLOGY",
                "kd_fungsi_bidang_lvl2": "",
                "nm_fungsi_bidang_lvl2": "",
                "kd_fungsi_bidang_lvl3": "",
                "kd_kantor": "100000000000000",
                "nm_kantor": "Kantor Pusat",
                "cmp_id": "CMP-000001",
                "perusahaan": "PT WIJAYA KARYA (PERSERO) Tbk.",
                "no_sk": "SK.02.01/A.DEP.HC.14770/2016",
                "tgl_sk": "2016-12-05",
                "kd_dep": "A",
                "ntname": "WIKA\\riha",
                "no_spk": None,
                "nama_real": None,
                "nama_proyek": None,
                "jns_organisasi": "PUSAT",
                "photo": "https://new-portal.wika.co.id/assets/images/user-5ce78adb5e913.jpg"
              }
        }
        jess = json.dumps(data)

        return jess