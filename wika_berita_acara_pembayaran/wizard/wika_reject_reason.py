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
        bap_model = self.env['wika.berita.acara.pembayaran'].sudo()

        # groups_id = self._context['groups_id']
        if active_id:
            bap_id = bap_model.browse([active_id])
            bap_id_model = bap_model.search([('id', '=', active_id)], limit=1)
            for x in bap_id.document_ids:
                x.write({
                    'state': 'rejected'
                })
            for y in min(bap_id_model.history_approval_ids, key=lambda x: x.id):
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': 4,
                    'res_model_id': self.env['ir.model'].sudo().search(
                        [('model', '=', 'wika.berita.acara.pembayaran')], limit=1).id,
                    'res_id': bap_id.id,
                    'user_id': y.user_id.id,
                    'nomor_po': bap_id_model.po_id.name,
                    'date_deadline': fields.Date.today() + timedelta(days=2),
                    'state': 'planned',
                    'status': 'todo',
                    'summary': """Document has been Reject, Please Re-upload Document!"""
                })
            for z in bap_id_model.activity_ids.filtered(lambda z: z.status == 'to_approve'):
                if z.user_id.id==self._uid:
                    z.status = 'approved'
                    z.action_done()

            self.env['wika.bap.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id,
                'date': datetime.now(),
                'note': "Reject (" + self.reject_reason + ")",
                'bap_id': active_id,
            })
            bap_id_model.write({
                'step_approve': bap_id_model.step_approve  -1,
                'state':'rejected'})

            return {'type': 'ir.actions.act_window_close'}
        