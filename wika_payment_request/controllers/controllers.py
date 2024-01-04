# -*- coding: utf-8 -*-
# from odoo import http


# class /home/firgy/project/wika/digitalInvoice/wikaPaymentRequest(http.Controller):
#     @http.route('//home/firgy/project/wika/digital_invoice/wika_payment_request//home/firgy/project/wika/digital_invoice/wika_payment_request', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//home/firgy/project/wika/digital_invoice/wika_payment_request//home/firgy/project/wika/digital_invoice/wika_payment_request/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('/home/firgy/project/wika/digital_invoice/wika_payment_request.listing', {
#             'root': '//home/firgy/project/wika/digital_invoice/wika_payment_request//home/firgy/project/wika/digital_invoice/wika_payment_request',
#             'objects': http.request.env['/home/firgy/project/wika/digital_invoice/wika_payment_request./home/firgy/project/wika/digital_invoice/wika_payment_request'].search([]),
#         })

#     @http.route('//home/firgy/project/wika/digital_invoice/wika_payment_request//home/firgy/project/wika/digital_invoice/wika_payment_request/objects/<model("/home/firgy/project/wika/digital_invoice/wika_payment_request./home/firgy/project/wika/digital_invoice/wika_payment_request"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/home/firgy/project/wika/digital_invoice/wika_payment_request.object', {
#             'object': obj
#         })
