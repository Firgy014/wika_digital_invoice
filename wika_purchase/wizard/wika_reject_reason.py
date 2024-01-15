from odoo import models, fields
from datetime import datetime, timedelta

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason')

    def cancel(self):
        return
    
    def ok(self):
        purchase_model = self.env['purchase.order'].sudo()
        active_id = self.env.context.get('active_id')

        model_id = self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
        if model_id:
            model_wika_id = self.env['wika.approval.setting'].search([('model_id', '=', model_id.id)], limit=1)

        if active_id:
            purchase_id = purchase_model.browse([active_id])
            groups_line = self.env['wika.approval.setting.line'].search([
                ('branch_id', '=', purchase_id.branch_id.id),
                ('sequence', '=', purchase_id.step_approve),
                ('approval_id', '=', model_wika_id.id)], limit=1)
            groups_id = groups_line.groups_id

            self.env['wika.po.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id.id,
                'date': datetime.now(),
                'note': "Reject (" + self.reject_reason + ")",
                'purchase_id': active_id,
            })
            return {'type': 'ir.actions.act_window_close'}        