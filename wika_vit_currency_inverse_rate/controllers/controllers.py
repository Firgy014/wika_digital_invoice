# -*- coding: utf-8 -*-
# from odoo import http


# class WikaVitCurrencyInverseRate(http.Controller):
#     @http.route('/wika_vit_currency_inverse_rate/wika_vit_currency_inverse_rate', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_vit_currency_inverse_rate/wika_vit_currency_inverse_rate/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_vit_currency_inverse_rate.listing', {
#             'root': '/wika_vit_currency_inverse_rate/wika_vit_currency_inverse_rate',
#             'objects': http.request.env['wika_vit_currency_inverse_rate.wika_vit_currency_inverse_rate'].search([]),
#         })

#     @http.route('/wika_vit_currency_inverse_rate/wika_vit_currency_inverse_rate/objects/<model("wika_vit_currency_inverse_rate.wika_vit_currency_inverse_rate"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_vit_currency_inverse_rate.object', {
#             'object': obj
#         })
