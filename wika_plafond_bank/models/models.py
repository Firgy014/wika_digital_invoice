# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class wika_flafond_bank(models.Model):
#     _name = 'wika_flafond_bank.wika_flafond_bank'
#     _description = 'wika_flafond_bank.wika_flafond_bank'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
