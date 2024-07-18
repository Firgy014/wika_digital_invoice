# -*- coding: utf-8 -*-
# from odoo import http


# class WikaReportLembarKendali(http.Controller):
#     @http.route('/wika_report_lembar_kendali/wika_report_lembar_kendali', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_report_lembar_kendali/wika_report_lembar_kendali/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_report_lembar_kendali.listing', {
#             'root': '/wika_report_lembar_kendali/wika_report_lembar_kendali',
#             'objects': http.request.env['wika_report_lembar_kendali.wika_report_lembar_kendali'].search([]),
#         })

#     @http.route('/wika_report_lembar_kendali/wika_report_lembar_kendali/objects/<model("wika_report_lembar_kendali.wika_report_lembar_kendali"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_report_lembar_kendali.object', {
#             'object': obj
#         })
