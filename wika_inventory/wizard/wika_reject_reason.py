from odoo import models, fields
from datetime import datetime, timedelta

class RejectWizardPicking(models.TransientModel):
    _name = 'reject.wizard.picking'
    _description = 'Reject Wizard Picking'

    reject_reason = fields.Text(string='Reject Reason')

    def cancel(self):
        return
    
    def ok(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            audit_log_obj = self.env['wika.picking.approval.line'].create({
                'user_id': self._uid,
                'date': datetime.now(),
                'note': "Reject ( " + self.reject_reason + " )",
                'picking_id': active_id,
            })
            return {'type': 'ir.actions.act_window_close'}
        