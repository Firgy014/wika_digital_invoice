# -*- coding: utf-8 -*-
# from odoo import http


# class WikaCashLoan(http.Controller):
#     @http.route('/wika_cash_loan/wika_cash_loan', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_cash_loan/wika_cash_loan/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_cash_loan.listing', {
#             'root': '/wika_cash_loan/wika_cash_loan',
#             'objects': http.request.env['wika_cash_loan.wika_cash_loan'].search([]),
#         })

#     @http.route('/wika_cash_loan/wika_cash_loan/objects/<model("wika_cash_loan.wika_cash_loan"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_cash_loan.object', {
#             'object': obj
#         })
