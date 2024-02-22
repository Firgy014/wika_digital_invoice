from odoo import models, fields
from datetime import datetime, timedelta

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard.account.move'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason')
    document_id = fields.Many2one('wika.document.setting', string='Document')

    def cancel(self):
        return

    def ok(self):
        groups_id = self.env.context.get('groups_id')
        active_id = self.env.context.get('active_id')
        am_model = self.env['account.move'].sudo()

        # groups_id = self._context['groups_id']
        if active_id:
            invoice_id = am_model.browse([active_id])
            invoice_id_model = am_model.search([('id', '=', active_id)], limit=1)
            for x in invoice_id.document_ids:
                if x.document_id.name == self.document_id.name:
                    x.write({
                        'state': 'rejected'
                    })
                    rejected_docname = self.document_id.name
                else:
                    rejected_docname = ''

            for y in min(invoice_id_model.history_approval_ids, key=lambda x: x.id):
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': 4,
                    'res_model_id': self.env['ir.model'].sudo().search(
                        [('model', '=', 'account.move')], limit=1).id,
                    'res_id': invoice_id.id,
                    'user_id': y.user_id.id,
                    'nomor_po': invoice_id_model.po_id.name,
                    'date_deadline': fields.Date.today() + timedelta(days=2),
                    'state': 'planned',
                    'status': 'todo',
                    'summary': """Document has been Reject, Please Re-upload Document!"""
                })
            for z in invoice_id_model.activity_ids.filtered(lambda z: z.status == 'to_approve'):
                if z.user_id.id==self._uid:
                    z.status = 'approved'
                    z.action_done()

            if rejected_docname != '':
                self.env['wika.invoice.approval.line'].create({
                    'user_id': self._uid,
                    'groups_id': groups_id,
                    'date': datetime.now(),
                    'note': f"Reject ({rejected_docname}): {self.reject_reason}",
                    'invoice_id': active_id,
                })
            else:
                self.env['wika.invoice.approval.line'].create({
                    'user_id': self._uid,
                    'groups_id': groups_id,
                    'date': datetime.now(),
                    'note': f"Reject ({self.reject_reason})",
                    'invoice_id': active_id,
                })
            invoice_id_model.write({
                'step_approve': 1,
                'state':'rejected'})

            return {'type': 'ir.actions.act_window_close'}

