from odoo import models, fields
from datetime import datetime, timedelta

class ApprovalWizard(models.TransientModel):
    _name = 'approval.wizard.account.move'
    _description = 'Approval Wizard'

    keterangan = fields.Html('Keterangan')

    def ok(self):
        return {'type': 'ir.actions.act_window_close'}
        # active_id = self.env.context.get('active_id')
        # am_model = self.env['account.move'].sudo()

        # if active_id:
        #     invoice_id = am_model.browse([active_id])
        #     invoice_id_model = am_model.search([('id', '=', active_id)], limit=1)
        #     for x in invoice_id:
        #         x.write({
        #             'state': 'approved'
        #         })
        # return {'type': 'ir.actions.act_window_close'}

    def cancel(self):
        return {'type': 'ir.actions.act_window_close'}