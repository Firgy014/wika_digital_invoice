from odoo import models, fields
from datetime import datetime, timedelta

class RejectWizard(models.TransientModel):
    _name = 'po.reject.wizard'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason')

    def cancel(self):
        return
    
    def ok(self):
        purchase_model = self.env['purchase.order'].sudo()
        groups_id = self.env.context.get('groups_id')
        active_id = self.env.context.get('active_id')
        print ("heheheeeeeeee")
        model_id = self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
        if model_id:
            model_wika_id = self.env['wika.approval.setting'].search([('model_id', '=', model_id.id)], limit=1)

        if active_id:
            print (active_id)
            purchase_id = purchase_model.browse([active_id])
            purchase_id_model = purchase_model.search([('id', '=', active_id)], limit=1)
            for x in purchase_id_model.document_ids:
                x.write({
                    'state': 'rejected'
                })
            for y in purchase_id_model.history_approval_ids.filtered(lambda y: y.note == 'Submit Document'):
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': 4,
                    'res_model_id': self.env['ir.model'].sudo().search(
                        [('model', '=', 'purchase.order')], limit=1).id,
                    'res_id': purchase_id.id,
                    'user_id': y.user_id.id,
                    'date_deadline': fields.Date.today() + timedelta(days=2),
                    'state': 'planned',
                    'status': 'todo',
                    'summary': """Document has been Reject, Please Re-upload Document!"""
                })
            for z in purchase_id_model.activity_ids.filtered(lambda z: z.status == 'to_approve'):
                if z.user_id.id==self._uid:
                    print ('llllllllllllll')
                    z.status = 'approved'
                    z.action_done()

            self.env['wika.po.approval.line'].create({
                'user_id': self._uid,
                'groups_id': groups_id,
                'date': datetime.now(),
                'note': "Reject (" + self.reject_reason + ")",
                'purchase_id': active_id,
            })
            purchase_id_model.write({
                'step_approve': purchase_id_model.step_approve  -1,
                'state':'rejected'})
            return {'type': 'ir.actions.act_window_close'}        