# -*- coding: utf-8 -*-
# from odoo import http


# class WikaDigitalInvoice(http.Controller):
#     @http.route('/wika_digital_invoice/wika_digital_invoice', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_digital_invoice/wika_digital_invoice/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_digital_invoice.listing', {
#             'root': '/wika_digital_invoice/wika_digital_invoice',
#             'objects': http.request.env['wika_digital_invoice.wika_digital_invoice'].search([]),
#         })

#     @http.route('/wika_digital_invoice/wika_digital_invoice/objects/<model("wika_digital_invoice.wika_digital_invoice"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_digital_invoice.object', {
#             'object': obj
#         })
