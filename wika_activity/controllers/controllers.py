# -*- coding: utf-8 -*-
# from odoo import http


# class WikaActivity(http.Controller):
#     @http.route('/wika_activity/wika_activity', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wika_activity/wika_activity/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wika_activity.listing', {
#             'root': '/wika_activity/wika_activity',
#             'objects': http.request.env['wika_activity.wika_activity'].search([]),
#         })

#     @http.route('/wika_activity/wika_activity/objects/<model("wika_activity.wika_activity"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wika_activity.object', {
#             'object': obj
#         })
