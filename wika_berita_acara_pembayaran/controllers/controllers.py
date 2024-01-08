# -*- coding: utf-8 -*-
# from odoo import http


# class /home/firgy/project/wika/digitalInvoice/wikaBeritaAcaraPembayaran(http.Controller):
#     @http.route('//home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran//home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran//home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('/home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran.listing', {
#             'root': '//home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran//home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran',
#             'objects': http.request.env['/home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran./home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran'].search([]),
#         })

#     @http.route('//home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran//home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran/objects/<model("/home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran./home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran.object', {
#             'object': obj
#         })
