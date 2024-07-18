# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class wika_sc_currency(models.Model):
#     _name = 'wika_sc_currency.wika_sc_currency'
#     _description = 'wika_sc_currency.wika_sc_currency'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
