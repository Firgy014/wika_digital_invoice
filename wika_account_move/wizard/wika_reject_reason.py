from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class RejectWizard(models.TransientModel):
    _name = 'reject.wizard.account.move'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason', required=True)
    related_document_ids = fields.Many2many('documents.document', string='Related Documents', domain=lambda self: [('purchase_id', '=', self._get_related_documents_domain()[0]), ('folder_id', 'in', self._get_related_documents_domain()[1])])
    is_reject_doc = fields.Boolean(string='Reject With Document')

    @api.model
    def _get_related_documents_domain(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            invoice_id = self.env['account.move'].sudo().browse([active_id])
            return invoice_id.po_id.id, ('PO', 'GR/SES', 'BAP', 'Invoicing')
        return False, ()

    def cancel(self):
        return
    
    def _get_first_user(self, groups_name, project_id):
        first_user_groups_id = self.env['res.groups'].sudo().search([('name', '=', groups_name)], limit=1)
        for first_user in first_user_groups_id.users:
            if project_id.sap_code in first_user.name:
                return first_user
            break

    def _get_mp_user(self, groups_name, project_id):
        mp_user_groups_id = self.env['res.groups'].sudo().search([('name', '=', groups_name)], limit=1)
        for mp_user in mp_user_groups_id.users:
            if 'MP' in mp_user.name and project_id.sap_code in mp_user.name:
                return mp_user
            break

    def ok(self):
        if self.is_reject_doc and not self.related_document_ids:
            raise ValidationError("Harap pilih dokumen-dokumen yang ingin di-reject!")

        groups_id = self.env.context.get('groups_id')
        active_id = self.env.context.get('active_id')
        am_model = self.env['account.move'].sudo()
        is_doc_rejection = False
        is_paralel_rejection = False
        is_able_to_reject_picking_doc = False

        if active_id:
            invoice_id = am_model.browse([active_id])
            invoice_id_model = am_model.search([('id', '=', active_id)], limit=1)
            project_id = self.env['project.project'].sudo().browse(invoice_id_model.project_id.id)

            # Reject with selected docs
            if self.is_reject_doc:
                document_list = []

                for doc in self.related_document_ids:
                    if doc.folder_id.name == 'PO':
                        if invoice_id_model.po_id.transaction_type == 'BTL':
                            first_user = self._get_first_user(groups_name='Kasie KA', project_id=project_id)
                        elif invoice_id_model.po_id.transaction_type == 'BL':
                            first_user = self._get_first_user(groups_name='Kasie Kom', project_id=project_id)

                        for x in invoice_id_model.po_id.document_ids:
                            x.state = 'rejected'
                            purchase_model_id = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
                            doc_setting_id = self.env['wika.document.setting'].sudo().search([('model_id', '=', purchase_model_id.id)])

                            if doc_setting_id:
                                for document_line in doc_setting_id:
                                    document_list.append((0, 0, {
                                        'invoice_id': invoice_id_model.id,
                                        'document_id': document_line.id,
                                        'state': 'rejected',
                                        'rejected_doc_id': doc.id
                                    }))

                        doc.active = False
                        is_doc_rejection = True

                    if doc.folder_id.name == 'Invoicing':
                        is_paralel_rejection = True
                        for x in invoice_id_model.document_ids.filtered(lambda x: x.document_id.name in ['Invoice', 'Faktur Pajak']):
                            x.write({
                                'state': 'rejected',
                                'document': False
                            })
                            doc.write({'active': False})
                            is_doc_rejection = True

                    if doc.folder_id.name == 'BAP':
                        if invoice_id_model.po_id.transaction_type == 'BTL':
                            first_user = self._get_first_user(groups_name='Kasie KA', project_id=project_id)
                        elif invoice_id_model.po_id.transaction_type == 'BL':
                            first_user = self._get_first_user(groups_name='Kasie Kom', project_id=project_id)

                        for x in invoice_id_model.bap_id.document_ids:
                            x.state = 'rejected'
                            bap_model_id = self.env['ir.model'].sudo().search([('model', '=', 'wika.berita.acara.pembayaran')], limit=1)
                            doc_setting_id = self.env['wika.document.setting'].sudo().search([('model_id', '=', bap_model_id.id)])

                            if doc_setting_id:
                                for document_line in doc_setting_id:
                                    document_list.append((0, 0, {
                                        'invoice_id': invoice_id_model.id,
                                        'document_id': document_line.id,
                                        'state': 'rejected',
                                        'rejected_doc_id': doc.id
                                    }))

                        doc.active = False
                        is_doc_rejection = True

                    if doc.folder_id.name == 'GR/SES' and doc.picking_id:
                        tags = doc.tag_ids.mapped('name')
                        if 'GR' in tags:
                            doc_setting_gr_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'GR')], limit=1)
                            if doc_setting_gr_id:
                                document_list.append((0, 0, {
                                    'invoice_id': invoice_id_model.id,
                                    'document_id': doc_setting_gr_id.id,
                                    'state': 'rejected',
                                    'picking_id': doc.picking_id.id,
                                    'rejected_doc_id': doc.id
                                }))
                                is_doc_rejection = True
                                is_able_to_reject_picking_doc = True

                        if 'Surat Jalan' in tags:
                            doc_setting_sj_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'Surat Jalan')], limit=1)
                            if doc_setting_sj_id:
                                document_list.append((0, 0, {
                                    'invoice_id': invoice_id_model.id,
                                    'document_id': doc_setting_sj_id.id,
                                    'state': 'rejected',
                                    'picking_id': doc.picking_id.id,
                                    'rejected_doc_id': doc.id
                                }))
                                is_doc_rejection = True
                                is_able_to_reject_picking_doc = True

                        if 'SES' in tags:
                            doc_setting_ses_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'SES')], limit=1)
                            if doc_setting_ses_id:
                                document_list.append((0, 0, {
                                    'invoice_id': invoice_id_model.id,
                                    'document_id': doc_setting_ses_id.id,
                                    'state': 'rejected',
                                    'picking_id': doc.picking_id.id,
                                    'rejected_doc_id': doc.id
                                }))
                                is_doc_rejection = True
                                is_able_to_reject_picking_doc = True

                        doc.active = False

                if len(document_list) > 0:
                    invoice_id.document_ids = document_list

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
                        'summary': """Document has been rejected, please re-upload document!"""
                    })

                for z in invoice_id_model.activity_ids.filtered(lambda z: z.status == 'to_approve'):
                    if z.user_id.id == self._uid:
                        z.status = 'approved'
                        z.action_done()

                if is_doc_rejection:
                    self.env['wika.invoice.approval.line'].create({
                        'user_id': self._uid,
                        'groups_id': groups_id,
                        'date': datetime.now(),
                        'note': "Reject with document: " + doc.folder_id.name + " (" + self.reject_reason + ")",
                        'invoice_id': active_id,
                    })
                else:
                    self.env['wika.invoice.approval.line'].create({
                        'user_id': self._uid,
                        'groups_id': groups_id,
                        'date': datetime.now(),
                        'note': "Reject (" + self.reject_reason + ")",
                        'invoice_id': active_id,
                    })
                invoice_id_model.write({
                    'step_approve': 1,
                    'state': 'rejected',
                    'is_paralel_rejection': is_paralel_rejection
                })

            for sip in invoice_id.document_ids:
                print('SIP_DIBAWAH', sip.document_id.name, sip.picking_id.name, sip.rejected_doc_id.name)

            if is_able_to_reject_picking_doc == True:
                for i in invoice_id.bap_id.bap_ids:
                    for j in i.picking_id.document_ids:
                        j.state = 'rejected'

        return {'type': 'ir.actions.act_window_close'}
