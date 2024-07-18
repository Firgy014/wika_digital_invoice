# -*- coding: utf-8 -*-
# from odoo import http


# class WikaScCurrency(http.Controller):
#     @http.route('/wika_sc_currency/wika_sc_currency', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_sc_currency/wika_sc_currency/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_sc_currency.listing', {
#             'root': '/wika_sc_currency/wika_sc_currency',
#             'objects': http.request.env['wika_sc_currency.wika_sc_currency'].search([]),
#         })

#     @http.route('/wika_sc_currency/wika_sc_currency/objects/<model("wika_sc_currency.wika_sc_currency"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_sc_currency.object', {
#             'object': obj
#         })
