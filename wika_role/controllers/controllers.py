# -*- coding: utf-8 -*-
# from odoo import http


# class WikaRole(http.Controller):
#     @http.route('/wika_role/wika_role', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_role/wika_role/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_role.listing', {
#             'root': '/wika_role/wika_role',
#             'objects': http.request.env['wika_role.wika_role'].search([]),
#         })

#     @http.route('/wika_role/wika_role/objects/<model("wika_role.wika_role"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_role.object', {
#             'object': obj
#         })
