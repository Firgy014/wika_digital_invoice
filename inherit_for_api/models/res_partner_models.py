#############################################################
#                                                                                    
#  Module Name: iniherit_partner                                                                            
#  Created On: 2019-02-19 14:34                                                                        
#  File Name: D:/MyData/Erwin/Odoo/odoo11e_wika/addons_custom/inherit_partner/models/budget_bad_models.py
#  Author: ACER                                                                                
#                                                                                                                         
#############################################################
# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


# from datetime import timedelta

class partner(models.Model):
    # ____________ ORM disini ____________ 
    _inherit = 'res.partner'

    def name_get(self):
        res = []
        for record in self:
            tit = "[%s] %s" % (record.kode_nasabah_baru, record.name)
            res.append((record.id, tit))
        return res

    def name_search(self, name, args=None, operator='ilike', limit=1000):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            args = ['|', '|', ('ref', operator, name), ('kode_nasabah_baru', operator, name),
                    ('name', operator, name)] + args
        categories = self.search(args, limit=limit)
        return categories.name_get()

    tipe_faktur = fields.Boolean(string='Tipe Faktur')
    name_cp = fields.Char(string='Nama Kontak')  # option: size=40, translate=False)
    function_cp = fields.Char(string='Function Kontak')  # option: size=40, translate=False)
    email_cp = fields.Char(string='Email Kontak')  # option: size=40, translate=False)
    phone_cp = fields.Char(string='Phone Kontak')  # option: size=40, translate=False)
    mobile_cp = fields.Char(string='Mobile Kontak')  # option: size=40, translate=False)
    nama_bank = fields.Char(string='Nama Bank')  # option: size=40, translate=False)
    cabang = fields.Char(string='Nama Cabang')  # option: size=40, translate=False)
    nomor_rekening = fields.Char(string='Nomor Rekening')  # option: size=40, translate=False)
    atas_nama = fields.Char(string='Atas Nama')  # option: size=40, translate=False)
    cotid = fields.Char(string='COT ID')  # option: size=40, translate=False)
    id_nasabah = fields.Char(string='ID Nasabah')
    kode_nasabah_baru = fields.Char(string='Kode Nasabah 8 Digit')
    sap_code    = fields.Char(string="Kode SAP")


