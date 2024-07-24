from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason', required=True)
    
    def cancel(self):
        return

    def ok(self):
        groups_id = self.env.context.get('groups_id')
        active_id = self.env.context.get('active_id')
        ncl_model = self.env['wika.noncash.loan'].sudo().browse(active_id)

        if active_id:
            ncl_id = ncl_model.browse([active_id])
            ncl_id_model = ncl_model.search([('id', '=', active_id)], limit=1)
            self.env['wika.noncash.loan.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id,
                'date': datetime.now(),
                'note': "Reject (" + self.reject_reason + ")",
                'ncl_id': active_id,
            })

            for activity in ncl_id_model.activity_ids.filtered(lambda x: x.status == 'to_approve' and x.user_id.id == self._uid):
                activity.status = 'approved'
                activity.action_done()

            stage_next = self.env['wika.loan.stage'].search([
                ('tipe', '=', 'Non Cash'),
                ('name', '=', 'Reject')
            ], limit=1)

            if not stage_next:
                raise ValidationError('Stage "Reject" tidak ditemukan. Silakan hubungi Administrator!')

            ncl_id_model.write({
                'stage_id': stage_next.id,
                'step_approve': 1
            })

            for approval_line in ncl_id_model.history_approval_ids:
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': 4,
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'wika.noncash.loan')], limit=1).id,
                    'res_id': active_id,
                    'user_id': approval_line.user_id.id,
                    'date_deadline': fields.Date.today() + timedelta(days=2),
                    'state': 'planned',
                    'status': 'todo',
                    'summary': "Document has been Reject, Please Re-upload Document!"
                })

            return {'type': 'ir.actions.act_window_close'}


