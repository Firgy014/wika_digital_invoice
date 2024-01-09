from odoo import models, fields
from datetime import datetime, timedelta

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard.account.move'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason')

    def cancel(self):
        return
    
    def ok(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            audit_log_obj = self.env['wika.invoice.approval.line'].create({'user_id': self._uid,
                'date': datetime.now(),
                'note': "Reject ( " + self.reject_reason + " )",
                'invoice_id': active_id,
                })
            return {'type': 'ir.actions.act_window_close'}
        