# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class wika_report_outstanding_bap(models.Model):
#     _name = 'wika_report_outstanding_bap.wika_report_outstanding_bap'
#     _description = 'wika_report_outstanding_bap.wika_report_outstanding_bap'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
