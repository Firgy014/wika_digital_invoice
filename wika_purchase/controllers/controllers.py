# -*- coding: utf-8 -*-
# from odoo import http


# class WikaPurchase(http.Controller):
#     @http.route('/wika_purchase/wika_purchase', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_purchase/wika_purchase/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_purchase.listing', {
#             'root': '/wika_purchase/wika_purchase',
#             'objects': http.request.env['wika_purchase.wika_purchase'].search([]),
#         })

#     @http.route('/wika_purchase/wika_purchase/objects/<model("wika_purchase.wika_purchase"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_purchase.object', {
#             'object': obj
#         })
