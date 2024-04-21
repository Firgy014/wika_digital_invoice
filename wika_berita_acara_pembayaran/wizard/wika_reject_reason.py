from datetime import datetime, timedelta
from odoo import models, fields, api

class RejectWizard(models.TransientModel):
    _name = 'reject.wizard'
    _description = 'Reject Wizard'

    reject_reason = fields.Text(string='Reject Reason')
    related_document_ids = fields.Many2many('documents.document', string='Related Documents', domain=lambda self: [('purchase_id', '=', self._get_related_documents_domain()[0]), ('folder_id', 'in', self._get_related_documents_domain()[1])])
    is_reject_doc = fields.Boolean(string='Reject With Document')

    @api.model
    def _get_related_documents_domain(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            bap_id = self.env['wika.berita.acara.pembayaran'].sudo().browse([active_id])
            return bap_id.po_id.id, ('PO', 'GR/SES', 'BAP')
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
        bap_model = self.env['wika.berita.acara.pembayaran'].sudo()

        # groups_id = self._context['groups_id']
        if active_id:
            bap_id = bap_model.browse([active_id])
            bap_id_model = bap_model.search([('id', '=', active_id)], limit=1)
            project_id = self.env['project.project'].sudo().browse(bap_id_model.project_id.id)

            # reject with selected docs
            if self.is_reject_doc == True:
                for doc in self.related_document_ids:
                    if doc.folder_id.name == 'PO':
                        if bap_id_model.po_id.transaction_type == 'BTL':
                            first_user = self._get_first_user(groups_name='Kasie KA', project_id=project_id)
                        elif bap_id_model.po_id.transaction_type == 'BL':
                            first_user = self._get_first_user(groups_name='Kasie Kom', project_id=project_id)

                        for x in bap_id_model.po_id.document_ids:
                            # self.env['mail.activity'].sudo().create({
                            #     'activity_type_id': 4,
                            #     'res_model_id': self.env['ir.model'].sudo().search(
                            #         [('model', '=', 'purchase.order')], limit=1).id,
                            #     'res_id': doc.purchase_id.id,
                            #     'user_id': first_user.id,
                            #     'date_deadline': fields.Date.today() + timedelta(days=2),
                            #     'state': 'planned',
                            #     'nomor_po': doc.purchase_id.name,
                            #     'status': 'todo',
                            #     'summary': f"""Dokumen {doc.folder_id.name} tidak sesuai dan telah di-reject. Silakan perbaiki dengan dokumen lain."""
                            # })
                            x.document = False
                            x.state = 'rejected'

                            document_list = []
                            purchase_model_id = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
                            doc_setting_id = self.env['wika.document.setting'].sudo().search([('model_id', '=', purchase_model_id.id)])

                            if doc_setting_id:
                                for document_line in doc_setting_id:
                                    document_list.append((0, 0, {
                                        'bap_id': bap_id_model.id,
                                        'document_id': document_line.id,
                                        'state': 'rejected'
                                    }))
                                bap_id.document_ids = document_list
                        doc.active = False
                        self.env['wika.bap.approval.line'].create({
                            'user_id': self._uid,
                            'groups_id': groups_id,
                            'date': datetime.now(),
                            'note': "Reject document:" + doc.folder_id.name + "(" + self.reject_reason + ")",
                            'bap_id': active_id,
                        })

                    elif doc.folder_id.name == 'GR/SES':
                        # for baps in bap_id_model.bap_ids:
                        if doc.picking_id.pick_type == 'gr':
                            first_user = self._get_first_user(groups_name='Kasie KA', project_id=project_id)
                        elif doc.picking_id.pick_type == 'ses':
                            first_user = self._get_first_user(groups_name='Kasie Kom', project_id=project_id)

                        for x in doc.picking_id.document_ids:                                
                            # self.env['mail.activity'].sudo().create({
                            #     'activity_type_id': 4,
                            #     'res_model_id': self.env['ir.model'].sudo().search(
                            #         [('model', '=', 'stock.picking')], limit=1).id,
                            #     'res_id': doc.picking_id.id,
                            #     'user_id': first_user.id,
                            #     'date_deadline': fields.Date.today() + timedelta(days=2),
                            #     'state': 'planned',
                            #     'nomor_po': doc.purchase_id.name,
                            #     'status': 'todo',
                            #     'summary': f"""Dokumen {doc.folder_id.name} tidak sesuai dan telah di-reject. Silakan perbaiki dengan dokumen lain."""
                            # })
                            x.document = False
                            x.state = 'rejected'

                            document_list = []

                            doc_setting_id = self.env['wika.document.setting'].sudo().search([('name', '=', x.document_id.name)], limit=1)

                    if doc_setting_id:
                        for document_line in doc_setting_id:
                            document_list.append((0, 0, {
                                'bap_id': bap_id_model.id,
                                'document_id': document_line.id,
                                'state': 'rejected',
                                'picking_id': doc.picking_id.id
                            }))
                        bap_id.document_ids = document_list
                    doc.active = False
                    self.env['wika.bap.approval.line'].create({
                        'user_id': self._uid,
                        'groups_id': groups_id,
                        'date': datetime.now(),
                        'note': "Reject document:" + doc.folder_id.name + "(" + self.reject_reason + ")",
                        'bap_id': active_id,
                    })

            # logical matrix to handle the reject without docs (x-z-z-x)
            for x in bap_id.document_ids:
                if len(self.related_document_ids) != len(bap_id.document_ids):
                    for z in self.related_document_ids:
                        if z.folder_id.name == 'BAP':
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
                    'summary': """Document has been rejected, Please Re-upload Document!"""
                })
            for z in bap_id_model.activity_ids.filtered(lambda z: z.status == 'to_approve'):
                if z.user_id.id == self._uid:
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
                'step_approve': 1,
                'state':'rejected'})

            return {'type': 'ir.actions.act_window_close'}