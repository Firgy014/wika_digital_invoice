# -*- coding: utf-8 -*-
# from odoo import http


# class WikaLoanApproval(http.Controller):
#     @http.route('/wika_loan_approval/wika_loan_approval', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_loan_approval/wika_loan_approval/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_loan_approval.listing', {
#             'root': '/wika_loan_approval/wika_loan_approval',
#             'objects': http.request.env['wika_loan_approval.wika_loan_approval'].search([]),
#         })

#     @http.route('/wika_loan_approval/wika_loan_approval/objects/<model("wika_loan_approval.wika_loan_approval"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_loan_approval.object', {
#             'object': obj
#         })
