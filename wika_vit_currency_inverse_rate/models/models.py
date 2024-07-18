# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class wika_vit_currency_inverse_rate(models.Model):
#     _name = 'wika_vit_currency_inverse_rate.wika_vit_currency_inverse_rate'
#     _description = 'wika_vit_currency_inverse_rate.wika_vit_currency_inverse_rate'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
