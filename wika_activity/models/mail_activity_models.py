# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Wika_Activity(models.Model):
    _inherit = 'mail.activity'

    status = fields.Selection([
        ('todo', 'To Upload'), 
        ('to_approve', 'To Approve'), 
        ('approved', 'Approved')
    ], string='Status', default='todo')
    user_ids = fields.Many2many(comodel_name='res.users', string='Assign Multiple Users')
    state = fields.Selection([
        ('overdue', 'Overdue'),
        ('today', 'Today'),
        ('planned', 'Planned')
    ], 'State', compute='_compute_state', store=True)

    # @api.depends('date_deadline')
    # def _compute_state(self):
    #     for record in self.filtered(lambda activity: activity.date_deadline):
    #         tz = record.user_id.sudo().tz
    #         date_deadline = record.date_deadline
    #         record.state = self._compute_state_from_date(date_deadline, tz)

    # @api.model
    # def _compute_state_from_date(self, date_deadline, tz=False):
    #     date_deadline = fields.Date.from_string(date_deadline)
    #     today_default = date.today()
    #     today = today_default
    #     if tz:
    #         today_utc = pytz.utc.localize(datetime.utcnow())
    #         today_tz = today_utc.astimezone(pytz.timezone(tz))
    #         today = date(year=today_tz.year, month=today_tz.month, day=today_tz.day)
    #     diff = (date_deadline - today)
    #     if diff.days == 0:
    #         return 'today'
    #     elif diff.days < 0:
    #         return 'overdue'
    #     else:
    #         return 'planned'
