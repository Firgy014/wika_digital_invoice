from odoo import models, fields
from datetime import datetime, timedelta

class Approval_Line_Wizard(models.TransientModel):
    _name = 'payment.request.line.wizard'
    _description = 'Payment Request Line Wizard'

    reject_reason = fields.Text(string='Reject Reason')

    def cancel(self):
        return
    
    def ok(self):
        # groups_id = self.env.context.get('groups_id')
        # active_id = self.env.context.get('active_id')
        # model_id = self.env['wika.payment.request'].sudo()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['wika.payment.request.line'].browse(active_ids):
            record.sudo().action_approve()
            # is_sent_to_sap = record.sudo().send_divisi_approved_pr_to_sap()
            # if is_sent_to_sap == True:
            #     record.sudo().send_pusat_approved_pr_to_sap()
        return {'type': 'ir.actions.act_window_close'}