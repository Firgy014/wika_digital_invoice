# -*- coding: utf-8 -*-
# from odoo import http


# class WikaDashboard(http.Controller):
#     @http.route('/wika_dashboard/wika_dashboard', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_dashboard/wika_dashboard/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_dashboard.listing', {
#             'root': '/wika_dashboard/wika_dashboard',
#             'objects': http.request.env['wika_dashboard.wika_dashboard'].search([]),
#         })

#     @http.route('/wika_dashboard/wika_dashboard/objects/<model("wika_dashboard.wika_dashboard"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_dashboard.object', {
#             'object': obj
#         })
