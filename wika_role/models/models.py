# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class wika_role(models.Model):
#     _name = 'wika_role.wika_role'
#     _description = 'wika_role.wika_role'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
