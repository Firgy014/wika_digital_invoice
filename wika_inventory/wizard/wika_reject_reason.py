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
        groups_id = self.env.context.get('groups_id')

        model_id = self.env['ir.model'].search([('model', '=', 'stock.picking')], limit=1)
        if active_id:

            picking_id_model = picking_model.search([('id', '=', active_id)], limit=1)
            for x in picking_id_model.document_ids:
                x.write({
                    'state': 'rejected'
                })
            for y in picking_id_model.history_approval_ids.filtered(lambda y: y.note == 'Submit Document'):
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': 4,
                    'res_model_id': self.env['ir.model'].sudo().search(
                        [('model', '=', 'stock.picking')], limit=1).id,
                    'res_id': active_id,
                    'user_id': y.user_id.id,
                    'nomor_po': picking_id_model.po_id.name,
                    'date_deadline': fields.Date.today() + timedelta(days=2),
                    'state': 'planned',
                    'status': 'todo',
                    'summary': """Document has been Reject, Please Re-upload Document!"""
                })
            for z in picking_id_model.activity_ids.filtered(lambda z: z.status == 'to_approve'):
                if z.user_id.id == self._uid:
                    z.status = 'approved'
                    z.action_done()

            self.env['wika.picking.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id,
                'date': datetime.now(),
                'note': "Reject (" + self.reject_reason + ")",
                'picking_id': active_id,
            })
            picking_id_model.write({
                'step_approve': picking_id_model.step_approve - 1,
                'state': 'rejected'})

            return {'type': 'ir.actions.act_window_close'}