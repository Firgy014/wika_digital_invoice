# -*- coding: utf-8 -*-
from odoo import http

# class McsProjek(http.Controller):
#     @http.route('/mcs_projek/mcs_projek/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_projek/mcs_projek/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_projek.listing', {
#             'root': '/mcs_projek/mcs_projek',
#             'objects': http.request.env['mcs_projek.mcs_projek'].search([]),
#         })

#     @http.route('/mcs_projek/mcs_projek/objects/<model("mcs_projek.mcs_projek"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_projek.object', {
#             'object': obj
#         })