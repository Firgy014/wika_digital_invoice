# -*- coding: utf-8 -*-
# from odoo import http


# class WikaBudgetManagement(http.Controller):
#     @http.route('/wika_budget_management/wika_budget_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_budget_management/wika_budget_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_budget_management.listing', {
#             'root': '/wika_budget_management/wika_budget_management',
#             'objects': http.request.env['wika_budget_management.wika_budget_management'].search([]),
#         })

#     @http.route('/wika_budget_management/wika_budget_management/objects/<model("wika_budget_management.wika_budget_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_budget_management.object', {
#             'object': obj
#         })
