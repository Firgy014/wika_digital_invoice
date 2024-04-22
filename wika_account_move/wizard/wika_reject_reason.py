from odoo import models, fields, api
from datetime import datetime, timedelta

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard.account.move'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    related_document_ids = fields.Many2many('documents.document', string='Related Documents', domain=lambda self: [('purchase_id', '=', self._get_related_documents_domain()[0]), ('folder_id', 'in', self._get_related_documents_domain()[1])])
    is_reject_doc = fields.Boolean(string='Reject With Document')

    @api.model
    def _get_related_documents_domain(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            invoice_id = self.env['account.move'].sudo().browse([active_id])
            return invoice_id.po_id.id, ('PO', 'GR/SES', 'BAP', 'Invoice', 'Faktur Pajak')
        return False, ()

    def cancel(self):
        return

    def _get_first_user(self, groups_name, project_id):
        first_user_groups_id = self.env['res.groups'].sudo().search([('name', '=', groups_name)], limit=1)
        for first_user in first_user_groups_id.users:
            if project_id.sap_code in first_user.name:
                return first_user

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
                'state':'rejected',
                'approval_stage': invoice_id_model.level,
            })

            return {'type': 'ir.actions.act_window_close'}

