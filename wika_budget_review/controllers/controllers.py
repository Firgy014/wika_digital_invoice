# -*- coding: utf-8 -*-
# from odoo import http


# class WikaBudgetReview(http.Controller):
#     @http.route('/wika_budget_review/wika_budget_review', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_budget_review/wika_budget_review/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_budget_review.listing', {
#             'root': '/wika_budget_review/wika_budget_review',
#             'objects': http.request.env['wika_budget_review.wika_budget_review'].search([]),
#         })

#     @http.route('/wika_budget_review/wika_budget_review/objects/<model("wika_budget_review.wika_budget_review"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_budget_review.object', {
#             'object': obj
#         })
