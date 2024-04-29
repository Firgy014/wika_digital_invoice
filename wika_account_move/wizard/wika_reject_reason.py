from odoo import models, fields, api
from datetime import datetime, timedelta

class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    def name_get(self):
        res = []
        for document in self:
            name = document.folder_id.name if document.folder_id else ''
            name += ' > ' + document.name if document.name != '' else ''
            res.append((document.id, name))
        return res

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard.account.move'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason')
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

    # def ok(self):
    #     groups_id = self.env.context.get('groups_id')
    #     active_id = self.env.context.get('active_id')
    #     am_model = self.env['account.move'].sudo()
    #     is_doc_rejection = False

    #     # groups_id = self._context['groups_id']
    #     if active_id:
    #         invoice_id = am_model.browse([active_id])
    #         invoice_id_model = am_model.search([('id', '=', active_id)], limit=1)
    #         project_id = self.env['project.project'].sudo().browse(invoice_id_model.bap_id.project_id.id)
    #         doc_setting_gr_id = False
    #         doc_setting_do_id = False
    #         doc_setting_ses_id = False
    #         doc_setting_inv_id = False
    #         doc_setting_fp_id = False
    #         document_list = list()

    #         # reject with selected docs
    #         if self.is_reject_doc == True:
    #             len_total_doc = len(invoice_id_model.document_ids) + len(self.related_document_ids)
    #             for doc in self.related_document_ids:
    #                 if doc.folder_id.name == 'PO':
    #                     if invoice_id_model.po_id.transaction_type == 'BTL':
    #                         first_user = self._get_first_user(groups_name='Kasie KA', project_id=project_id)
    #                     elif invoice_id_model.po_id.transaction_type == 'BL':
    #                         first_user = self._get_first_user(groups_name='Kasie Kom', project_id=project_id)

    #                     for x in invoice_id_model.po_id.document_ids:
    #                         x.state = 'rejected'
    #                         document_list = []
    #                         purchase_model_id = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
    #                         doc_setting_id = self.env['wika.document.setting'].sudo().search([('model_id', '=', purchase_model_id.id)])

    #                     if doc_setting_id:
    #                         for document_line in doc_setting_id:
    #                             document_list.append((0, 0, {
    #                                 'invoice_id': invoice_id_model.id,
    #                                 'document_id': document_line.id,
    #                                 'state': 'rejected'
    #                             }))
    #                         invoice_id.document_ids = document_list
    #                     doc.active = False
    #                     is_doc_rejection = True

    #                 elif doc.folder_id.name == 'GR/SES':
    #                     if doc.picking_id.pick_type == 'gr':
    #                         first_user = self._get_first_user(groups_name='Kasie KA', project_id=project_id)
    #                     elif doc.picking_id.pick_type == 'ses':
    #                         first_user = self._get_first_user(groups_name='Kasie Kom', project_id=project_id)

    #                     for x in doc.picking_id.document_ids:
    #                         if x.document_id.name == 'GR':
    #                             doc_setting_gr_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'GR')], limit=1)

    #                         if x.document_id.name == 'Surat Jalan':
    #                             doc_setting_do_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'Surat Jalan')], limit=1)
                                
    #                         if x.document_id.name == 'SES':
    #                             doc_setting_ses_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'SES')], limit=1)

    #                         x.state = 'rejected'
    #                         document_list = []

    #                 if doc_setting_gr_id and doc_setting_do_id:
    #                     for document_line_gr, document_line_do in zip(doc_setting_gr_id, doc_setting_do_id):
    #                         document_list.append((0, 0, {
    #                             'invoice_id': invoice_id_model.id,
    #                             'document_id': document_line_do.id,
    #                             'state': 'rejected'
    #                         }))
    #                         document_list.append((0, 0, {
    #                             'invoice_id': invoice_id_model.id,
    #                             'document_id': document_line_gr.id,
    #                             'state': 'rejected'
    #                         }))
    #                 if doc_setting_ses_id:
    #                     for document_line_ses in doc_setting_ses_id:
    #                         document_list.append((0, 0, {
    #                             'invoice_id': invoice_id_model.id,
    #                             'document_id': document_line_ses.id,
    #                             'state': 'rejected'
    #                         }))
                    
    #                 elif doc.folder_id.name == 'BAP':
    #                     if invoice_id_model.bap_id.po_id.transaction_type == 'BTL':
    #                         first_user = self._get_first_user(groups_name='Kasie KA', project_id=project_id)
    #                     elif invoice_id_model.bap_id.po_id.transaction_type == 'BL':
    #                         first_user = self._get_first_user(groups_name='Kasie Kom', project_id=project_id)

    #                     for x in doc.bap_id.document_ids:
    #                         if x.document_id.name == 'BAP':
    #                             doc_setting_bap_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'BAP')], limit=1)

    #                         x.state = 'rejected'
    #                         document_list = []

    #                     if doc_setting_bap_id:
    #                         for document_line_bap in doc_setting_bap_id:
    #                             document_list.append((0, 0, {
    #                                 'invoice_id': invoice_id_model.id,
    #                                 'document_id': document_line_bap.id,
    #                                 'state': 'rejected'
    #                             }))

    #                 invoice_id.document_ids = document_list
    #                 doc.active = False
    #                 is_doc_rejection = True
    #                 if len(invoice_id.document_ids) == len_total_doc:
    #                     break

    #         # logical matrix to handle the reject without docs (x-z-z-x)
    #         for x in invoice_id.document_ids:
    #             if len(self.related_document_ids) != len(invoice_id.document_ids):
    #                 for z in self.related_document_ids:
    #                     if z.folder_id.name == 'Invoice' or z.folder_id.name == 'Faktur Pajak':
    #                         x.write({
    #                             'state': 'rejected'
    #                         })

    #         # for x in invoice_id.document_ids:
    #         #     if x.document_id.name == self.document_id.name:
    #         #         x.write({
    #         #             'state': 'rejected'
    #         #         })
    #         #         rejected_docname = self.document_id.name
    #         #     else:
    #         #         rejected_docname = ''

    #         for y in min(invoice_id_model.history_approval_ids, key=lambda x: x.id):
    #             self.env['mail.activity'].sudo().create({
    #                 'activity_type_id': 4,
    #                 'res_model_id': self.env['ir.model'].sudo().search(
    #                     [('model', '=', 'account.move')], limit=1).id,
    #                 'res_id': invoice_id.id,
    #                 'user_id': y.user_id.id,
    #                 'nomor_po': invoice_id_model.po_id.name,
    #                 'date_deadline': fields.Date.today() + timedelta(days=2),
    #                 'state': 'planned',
    #                 'status': 'todo',
    #                 'summary': """Document has been rejected, please re-upload document!"""
    #             })
    #         for z in invoice_id_model.activity_ids.filtered(lambda z: z.status == 'to_approve'):
    #             if z.user_id.id == self._uid:
    #                 z.status = 'approved'
    #                 z.action_done()

    #         # if rejected_docname != '':
    #         #     self.env['wika.invoice.approval.line'].create({
    #         #         'user_id': self._uid,
    #         #         'groups_id': groups_id,
    #         #         'date': datetime.now(),
    #         #         'note': f"Reject ({rejected_docname}): {self.reject_reason}",
    #         #         'invoice_id': active_id,
    #         #     })
    #         if is_doc_rejection:
    #             self.env['wika.invoice.approval.line'].create({
    #                 'user_id': self._uid,
    #                 'groups_id': groups_id,
    #                 'date': datetime.now(),
    #                 'note': "Reject with document: " + doc.folder_id.name + " (" + self.reject_reason + ")",
    #                 'invoice_id': active_id,
    #             })
    #         else:
    #             self.env['wika.invoice.approval.line'].create({
    #                 'user_id': self._uid,
    #                 'groups_id': groups_id,
    #                 'date': datetime.now(),
    #                 'note': f"Reject ({self.reject_reason})",
    #                 'invoice_id': active_id,
    #             })
    #         invoice_id_model.write({
    #             'step_approve': 1,
    #             'state':'rejected',
    #             'approval_stage': invoice_id_model.level,
    #         })

    #         return {'type': 'ir.actions.act_window_close'}



    def ok(self):
        groups_id = self.env.context.get('groups_id')
        active_id = self.env.context.get('active_id')
        am_model = self.env['account.move'].sudo()
        is_doc_rejection = False

        # groups_id = self._context['groups_id']
        if active_id:
            invoice_id = am_model.browse([active_id])
            invoice_id_model = am_model.search([('id', '=', active_id)], limit=1)
            project_id = self.env['project.project'].sudo().browse(invoice_id_model.bap_id.project_id.id)
            doc_setting_gr_id = False
            doc_setting_do_id = False
            doc_setting_ses_id = False
            doc_setting_inv_id = False
            doc_setting_fp_id = False
            document_list = list()

            # reject with selected docs
            if self.is_reject_doc == True:
                len_total_doc = len(invoice_id_model.document_ids) + len(self.related_document_ids)
                document_list = []
                for doc in self.related_document_ids:
                    if len(invoice_id.document_ids) == 3:
                        break 
                    if doc.folder_id.name == 'PO':
                        if invoice_id_model.po_id.transaction_type == 'BTL':
                            first_user = self._get_first_user(groups_name='Kasie KA', project_id=project_id)
                        elif invoice_id_model.po_id.transaction_type == 'BL':
                            first_user = self._get_first_user(groups_name='Kasie Kom', project_id=project_id)

                        for index, x in enumerate(invoice_id_model.po_id.document_ids):
                            x.state = 'rejected'
                            purchase_model_id = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
                            doc_setting_id = self.env['wika.document.setting'].sudo().search([('model_id', '=', purchase_model_id.id)])

                            if doc_setting_id:
                                for document_line in doc_setting_id:
                                    document_list.append((0, 0, {
                                        'invoice_id': invoice_id_model.id,
                                        'document_id': document_line.id,
                                        'state': 'rejected'
                                    }))
                                invoice_id.document_ids = document_list
                            doc.active = False
                            is_doc_rejection = True
                            break  # Exit the loop after the first document is processed

                    elif doc.folder_id.name == 'GR/SES':

                        if doc.picking_id.pick_type == 'gr':
                            first_user = self._get_first_user(groups_name='Kasie KA', project_id=project_id)
                        elif doc.picking_id.pick_type == 'ses':
                            first_user = self._get_first_user(groups_name='Kasie Kom', project_id=project_id)

                        for x in doc.picking_id.document_ids:
                            if x.document_id.name == 'GR':
                                doc_setting_gr_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'GR')], limit=1)

                            if x.document_id.name == 'Surat Jalan':
                                doc_setting_do_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'Surat Jalan')], limit=1)
                                
                            if x.document_id.name == 'SES':
                                doc_setting_ses_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'SES')], limit=1)
                                if doc_setting_ses_id:
                                    # masooooookkkkk
                                    for document_line_ses in doc_setting_ses_id:
                                        document_list.append((0, 0, {
                                            'invoice_id': invoice_id_model.id,
                                            'document_id': document_line_ses.id,
                                            'state': 'rejected'
                                        }))
                                        invoice_id.document_ids = document_list

                            x.state = 'rejected'

                    if doc_setting_gr_id and doc_setting_do_id:
                        for document_line_gr, document_line_do in zip(doc_setting_gr_id, doc_setting_do_id):
                            document_list.append((0, 0, {
                                'invoice_id': invoice_id_model.id,
                                'document_id': document_line_do.id,
                                'state': 'rejected'
                            }))
                            document_list.append((0, 0, {
                                'invoice_id': invoice_id_model.id,
                                'document_id': document_line_gr.id,
                                'state': 'rejected'
                            }))
                    # if doc_setting_ses_id:
                    #     for document_line_ses in doc_setting_ses_id:
                    #         document_list.append((0, 0, {
                    #             'invoice_id': invoice_id_model.id,
                    #             'document_id': document_line_ses.id,
                    #             'state': 'rejected'
                    #         }))
                    
                    elif doc.folder_id.name == 'BAP':
                        if invoice_id_model.bap_id.po_id.transaction_type == 'BTL':
                            first_user = self._get_first_user(groups_name='Kasie KA', project_id=project_id)
                        elif invoice_id_model.bap_id.po_id.transaction_type == 'BL':
                            first_user = self._get_first_user(groups_name='Kasie Kom', project_id=project_id)

                        for x in doc.bap_id.document_ids:
                            if x.document_id.name == 'BAP':
                                doc_setting_bap_id = self.env['wika.document.setting'].sudo().search([('name', '=', 'BAP')], limit=1)

                            x.state = 'rejected'
                            document_list = []

                        if doc_setting_bap_id:
                            for document_line_bap in doc_setting_bap_id:
                                document_list.append((0, 0, {
                                    'invoice_id': invoice_id_model.id,
                                    'document_id': document_line_bap.id,
                                    'state': 'rejected'
                                }))
                                invoice_id.document_ids = document_list
                                
                    doc.active = False
                    is_doc_rejection = True
                    if len(invoice_id.document_ids) == len_total_doc:
                        break

            # logical matrix to handle the reject without docs (x-z-z-x)
            for x in invoice_id.document_ids:
                if len(self.related_document_ids) != len(invoice_id.document_ids):
                    for z in self.related_document_ids:
                        if z.folder_id.name == 'Invoice' or z.folder_id.name == 'Faktur Pajak':
                            x.write({
                                'state': 'rejected'
                            })

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
                    'note': f"Reject ({self.reject_reason})",
                    'invoice_id': active_id,
                })
            invoice_id_model.write({
                'step_approve': 1,
                'state':'rejected',
                'approval_stage': invoice_id_model.level,
            })


            # return {'type': 'ir.actions.act_window_close'}
