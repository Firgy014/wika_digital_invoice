from odoo import models, fields
from datetime import datetime, timedelta

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason')

    def cancel(self):
        return
    
    def ok(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            audit_log_obj = self.env['wika.po.approval.line'].create({'user_id': self._uid,
                'date': datetime.now(),
                'note': "Reject ( " + self.reject_reason + " )",
                'purchase_id': active_id,
                })
            return {'type': 'ir.actions.act_window_close'}
        