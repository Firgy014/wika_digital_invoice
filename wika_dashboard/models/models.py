from odoo import api, fields, models

class InheritMailActivity(models.Model):
    _inherit = "mail.activity"

    def action_open_document(self):
        """ Opens the related record based on the model and ID """
        self.ensure_one()
        if self.res_model == 'purchase.order':
            return {
                'res_id': self.res_id,
                'res_model': self.res_model,
                'target': 'current',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('wika_purchase.purchase_order_form_wika').id,
            }
        else:
            return {
                'res_id': self.res_id,
                'res_model': self.res_model,
                'target': 'current',
                'type': 'ir.actions.act_window',
                'view_mode': 'form'
            }