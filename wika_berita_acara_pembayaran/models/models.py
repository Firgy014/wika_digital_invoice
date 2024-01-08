# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class /home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran(models.Model):
#     _name = '/home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran./home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran'
#     _description = '/home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran./home/firgy/project/wika/digital_invoice/wika_berita_acara_pembayaran'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
