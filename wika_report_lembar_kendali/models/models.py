# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class wika_report_lembar_kendali(models.Model):
#     _name = 'wika_report_lembar_kendali.wika_report_lembar_kendali'
#     _description = 'wika_report_lembar_kendali.wika_report_lembar_kendali'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
