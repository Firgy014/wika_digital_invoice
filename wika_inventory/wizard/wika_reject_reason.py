from odoo import models, fields
from datetime import datetime, timedelta

class RejectWizardPicking(models.TransientModel):
    _name = 'reject.wizard.picking'
    _description = 'Reject Wizard Picking'

    reject_reason = fields.Text(string='Reject Reason')

    def cancel(self):
        return
    
    def ok(self):
        picking_model = self.env['stock.picking'].sudo()
        active_id = self.env.context.get('active_id')

        model_id = self.env['ir.model'].search([('model', '=', 'stock.picking')], limit=1)
        if model_id:
            model_wika_id = self.env['wika.approval.setting'].search([('model_id', '=', model_id.id)], limit=1)

        if active_id:
            picking_id = picking_model.browse([active_id])
            groups_line = self.env['wika.approval.setting.line'].search([
                ('branch_id', '=', picking_id.branch_id.id),
                ('sequence', '=', picking_id.step_approve),
                ('approval_id', '=', model_wika_id.id)], limit=1)
            groups_id = groups_line.groups_id

            self.env['wika.picking.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id.id,
                'date': datetime.now(),
                'note': "Reject (" + self.reject_reason + ")",
                'picking_id': active_id,
            })
            return {'type': 'ir.actions.act_window_close'}