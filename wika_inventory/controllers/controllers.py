# -*- coding: utf-8 -*-
# from odoo import http


# class Src/wikaDigitalInvoicing/addons/digitalInvoice/wikaInventory(http.Controller):
#     @http.route('/src/wika_digital_invoicing/addons/digital_invoice/wika_inventory/src/wika_digital_invoicing/addons/digital_invoice/wika_inventory', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/src/wika_digital_invoicing/addons/digital_invoice/wika_inventory/src/wika_digital_invoicing/addons/digital_invoice/wika_inventory/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('src/wika_digital_invoicing/addons/digital_invoice/wika_inventory.listing', {
#             'root': '/src/wika_digital_invoicing/addons/digital_invoice/wika_inventory/src/wika_digital_invoicing/addons/digital_invoice/wika_inventory',
#             'objects': http.request.env['src/wika_digital_invoicing/addons/digital_invoice/wika_inventory.src/wika_digital_invoicing/addons/digital_invoice/wika_inventory'].search([]),
#         })

#     @http.route('/src/wika_digital_invoicing/addons/digital_invoice/wika_inventory/src/wika_digital_invoicing/addons/digital_invoice/wika_inventory/objects/<model("src/wika_digital_invoicing/addons/digital_invoice/wika_inventory.src/wika_digital_invoicing/addons/digital_invoice/wika_inventory"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('src/wika_digital_invoicing/addons/digital_invoice/wika_inventory.object', {
#             'object': obj
#         })
