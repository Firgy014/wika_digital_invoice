# -*- coding: utf-8 -*-
# from odoo import http


# class /home/firgy/project/wika/digitalInvoice/wikaAccountMove(http.Controller):
#     @http.route('//home/firgy/project/wika/digital_invoice/wika_account_move//home/firgy/project/wika/digital_invoice/wika_account_move', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//home/firgy/project/wika/digital_invoice/wika_account_move//home/firgy/project/wika/digital_invoice/wika_account_move/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('/home/firgy/project/wika/digital_invoice/wika_account_move.listing', {
#             'root': '//home/firgy/project/wika/digital_invoice/wika_account_move//home/firgy/project/wika/digital_invoice/wika_account_move',
#             'objects': http.request.env['/home/firgy/project/wika/digital_invoice/wika_account_move./home/firgy/project/wika/digital_invoice/wika_account_move'].search([]),
#         })

#     @http.route('//home/firgy/project/wika/digital_invoice/wika_account_move//home/firgy/project/wika/digital_invoice/wika_account_move/objects/<model("/home/firgy/project/wika/digital_invoice/wika_account_move./home/firgy/project/wika/digital_invoice/wika_account_move"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/home/firgy/project/wika/digital_invoice/wika_account_move.object', {
#             'object': obj
#         })
