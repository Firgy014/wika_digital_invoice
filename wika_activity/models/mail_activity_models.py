# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Wika_Activity(models.Model):
    _inherit = 'mail.activity'

    status = fields.Selection([
        ('todo', 'To Do'), 
        ('approved', 'Approved')
    ], string='Status', default='todo')
    user_ids = fields.Many2many(comodel_name='res.users',string='Assign Multiple Users')
