# -*- coding: utf-8 -*-
# from odoo import http


# class WikaFlafondBank(http.Controller):
#     @http.route('/wika_flafond_bank/wika_flafond_bank', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_flafond_bank/wika_flafond_bank/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_flafond_bank.listing', {
#             'root': '/wika_flafond_bank/wika_flafond_bank',
#             'objects': http.request.env['wika_flafond_bank.wika_flafond_bank'].search([]),
#         })

#     @http.route('/wika_flafond_bank/wika_flafond_bank/objects/<model("wika_flafond_bank.wika_flafond_bank"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_flafond_bank.object', {
#             'object': obj
#         })
