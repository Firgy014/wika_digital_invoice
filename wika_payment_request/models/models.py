# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class /home/firgy/project/wika/digital_invoice/wika_payment_request(models.Model):
#     _name = '/home/firgy/project/wika/digital_invoice/wika_payment_request./home/firgy/project/wika/digital_invoice/wika_payment_request'
#     _description = '/home/firgy/project/wika/digital_invoice/wika_payment_request./home/firgy/project/wika/digital_invoice/wika_payment_request'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
