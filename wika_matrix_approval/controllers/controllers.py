# -*- coding: utf-8 -*-
# from odoo import http


# class WikaMatrixApproval(http.Controller):
#     @http.route('/wika_matrix_approval/wika_matrix_approval', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_matrix_approval/wika_matrix_approval/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_matrix_approval.listing', {
#             'root': '/wika_matrix_approval/wika_matrix_approval',
#             'objects': http.request.env['wika_matrix_approval.wika_matrix_approval'].search([]),
#         })

#     @http.route('/wika_matrix_approval/wika_matrix_approval/objects/<model("wika_matrix_approval.wika_matrix_approval"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_matrix_approval.object', {
#             'object': obj
#         })
