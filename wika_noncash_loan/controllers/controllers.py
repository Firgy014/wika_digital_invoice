# -*- coding: utf-8 -*-
# from odoo import http


# class WikaNoncashLoan(http.Controller):
#     @http.route('/wika_noncash_loan/wika_noncash_loan', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_noncash_loan/wika_noncash_loan/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_noncash_loan.listing', {
#             'root': '/wika_noncash_loan/wika_noncash_loan',
#             'objects': http.request.env['wika_noncash_loan.wika_noncash_loan'].search([]),
#         })

#     @http.route('/wika_noncash_loan/wika_noncash_loan/objects/<model("wika_noncash_loan.wika_noncash_loan"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_noncash_loan.object', {
#             'object': obj
#         })
