from odoo import models, fields
from datetime import datetime, timedelta

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard.pr'
    _description = 'Reject Wizard'

    reject_reason_pr = fields.Text(string='Reject Reason')

    def cancel(self):
        return
    
    def ok(self):
        active_id = self.env.context.get('active_id')
        # groups_id = self._context['groups_id']
        if active_id:
            audit_log_obj = self.env['wika.pr.approval.line'].create({'user_id': self._uid,
                # 'groups_id': groups_id,
                'date': datetime.now(),
                'note': "Reject ( " + self.reject_reason_pr + " )",
                'pr_id': active_id,
                })
            return {'type': 'ir.actions.act_window_close'}
        