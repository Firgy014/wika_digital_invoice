from odoo import models, fields
from datetime import datetime, timedelta

class ApprovalWizard(models.TransientModel):
    _name = 'approval.wizard.account.move'
    _description = 'Approval Wizard'

    keterangan = fields.Html('Keterangan')
    step_approve = fields.Integer(string='Step Approve')

    def ok(self):
        invoice_id = self.env.context.get('active_id')
        if invoice_id:
            invoice = self.env['account.move'].browse(invoice_id)
            current_step_approve = invoice.step_approve
            
            if current_step_approve > 1:
                current_step_approve -= 1
            
            model_id = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
            approval_id = self.env['wika.approval.setting'].sudo().search(
                [('model_id', '=', model_id.id)], limit=1)
            
            approval_line_id = self.env['wika.approval.setting.line'].search([
                ('sequence', '=', current_step_approve),
                ('approval_id', '=', approval_id.id)
            ], limit=1)
            
            groups_id = approval_line_id.groups_id
            self.env['wika.invoice.approval.line'].create({
                'user_id': self.env.user.id,
                'groups_id': groups_id.id,
                'date': fields.Datetime.now(),
                'note': 'Verified',
                'invoice_id': invoice_id,
                'information': self.keterangan,
                'is_show_wizard': True,  
            })
            return {'type': 'ir.actions.act_window_close'}
        else:
            return False
            
    def cancel(self):
        invoice_id = self.env.context.get('active_id')
        if invoice_id:
            invoice = self.env['account.move'].browse(invoice_id)
            if invoice.step_approve:
                invoice.step_approve -= 1
            
            return {'type': 'ir.actions.act_window_close'}
        else:
            return False