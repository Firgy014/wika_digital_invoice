from odoo import models, fields
from datetime import datetime, timedelta

class RejectWizard(models.TransientModel):
    _name = 'partial.reject.wizard.pr'
    _description = 'Partial Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason')

    def cancel(self):
        return
    
    def ok(self):
        groups_id = self.env.context.get('groups_id')
        active_id = self.env.context.get('active_id')
        partial_model = self.env['wika.partial.payment.request'].sudo()

        # groups_id = self._context['groups_id']
        if active_id:
            partial_id = partial_model.browse([active_id])
            partial_id_model = partial_model.search([('id', '=', active_id)], limit=1)
            for x in partial_id.document_ids:
                x.write({
                    'state': 'rejected'
                })
            for y in min(partial_id_model.history_approval_ids, key=lambda x: x.id):
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': 4,
                    'res_model_id': self.env['ir.model'].sudo().search(
                        [('model', '=', 'wika.partial.payment.request')], limit=1).id,
                    'res_id': partial_id.id,
                    'user_id': y.user_id.id,
                    'nomor_po': partial_id_model.invoice_id.po_id.name,
                    'date_deadline': fields.Date.today() + timedelta(days=2),
                    'state': 'planned',
                    'status': 'todo',
                    'summary': """Document has been Reject, Please Re-upload Document!"""
                })
            for z in partial_id_model.activity_ids.filtered(lambda z: z.status == 'to_approve'):
                if z.user_id.id==self._uid:
                    z.status = 'approved'
                    z.action_done()

            self.env['wika.partial.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id,
                'date': datetime.now(),
                'note': "Reject (" + self.reject_reason + ")",
                'pr_id': active_id,
            })
            partial_id_model.write({
                'step_approve': 1,
                'state':'rejected'})

            return {'type': 'ir.actions.act_window_close'}
