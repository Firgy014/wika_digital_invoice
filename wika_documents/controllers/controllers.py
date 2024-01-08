# -*- coding: utf-8 -*-
# from odoo import http


# class WikaDocuments(http.Controller):
#     @http.route('/wika_documents/wika_documents', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_documents/wika_documents/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_documents.listing', {
#             'root': '/wika_documents/wika_documents',
#             'objects': http.request.env['wika_documents.wika_documents'].search([]),
#         })

#     @http.route('/wika_documents/wika_documents/objects/<model("wika_documents.wika_documents"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_documents.object', {
#             'object': obj
#         })
