# -*- coding: utf-8 -*-
# from odoo import http


# class WikaReportOutstandingBap(http.Controller):
#     @http.route('/wika_report_outstanding_bap/wika_report_outstanding_bap', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_report_outstanding_bap/wika_report_outstanding_bap/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_report_outstanding_bap.listing', {
#             'root': '/wika_report_outstanding_bap/wika_report_outstanding_bap',
#             'objects': http.request.env['wika_report_outstanding_bap.wika_report_outstanding_bap'].search([]),
#         })

#     @http.route('/wika_report_outstanding_bap/wika_report_outstanding_bap/objects/<model("wika_report_outstanding_bap.wika_report_outstanding_bap"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_report_outstanding_bap.object', {
#             'object': obj
#         })
