# -*- coding: utf-8 -*-
# from odoo import http


# class WikaBudgetGenerateRkap(http.Controller):
#     @http.route('/wika_budget_generate_rkap/wika_budget_generate_rkap', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_budget_generate_rkap/wika_budget_generate_rkap/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_budget_generate_rkap.listing', {
#             'root': '/wika_budget_generate_rkap/wika_budget_generate_rkap',
#             'objects': http.request.env['wika_budget_generate_rkap.wika_budget_generate_rkap'].search([]),
#         })

#     @http.route('/wika_budget_generate_rkap/wika_budget_generate_rkap/objects/<model("wika_budget_generate_rkap.wika_budget_generate_rkap"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_budget_generate_rkap.object', {
#             'object': obj
#         })
