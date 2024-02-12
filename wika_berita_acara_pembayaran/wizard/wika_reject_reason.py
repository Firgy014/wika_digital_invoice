from odoo import models, fields
from datetime import datetime, timedelta

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason')

    def cancel(self):
        return
    
    def ok(self):
        groups_id = self.env.context.get('groups_id')
        active_id = self.env.context.get('active_id')

        # groups_id = self._context['groups_id']
        if active_id:
            audit_log_obj = self.env['wika.bap.approval.line'].create({'user_id': self._uid,
                'groups_id': groups_id.id,
                'datetime': datetime.now(),
                'note': "Reject ( " + self.reject_reason + " )",
                'bap_id': active_id,
                })
            return {'type': 'ir.actions.act_window_close'}
        