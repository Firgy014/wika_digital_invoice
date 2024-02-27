from odoo import api, fields, models

class InheritMailActivity(models.Model):
    _inherit = "mail.activity"

    res_model_name = fields.Char(string='Menu', related='res_model_id.name')
    nomor_po    =fields.Char(string='Nomor PO')
    branch_id = fields.Many2one('res.branch', string='Divisi', compute='_compute_branch_project_ids')
    project_id = fields.Many2one('project.project', string='Project', compute='_compute_branch_project_ids')
    conv_menu = fields.Char('Menu Convert')
    conv_project = fields.Char('Proyek')
    conv_division = fields.Char('Divisi')

    # @api.depends('res_id', 'res_model_id')
    # def _compute_branch_project_ids(self):
    #     for activity in self:
    #         if activity.res_model_id.model:
    #             print("MASUKKK", activity.res_model_id.model)
    #             res_model = self.env[activity.res_model_id.model].search([('id', '=', activity.res_id)], limit=1)
    #             if res_model:
    #                 activity.branch_id = res_model.branch_id.id
    #                 activity.project_id = res_model.project_id.id
    #         if activity.branch_id is False:
    #             activity.branch_id = self.env['res.branch'].search([], limit=1).id
    #         if activity.project_id is False:
    #             activity.project_id = self.env['project.project'].search([], limit=1).id

    @api.depends('res_id', 'res_model_id')
    def _compute_branch_project_ids(self):
        for activity in self:
            if activity.res_model_id.model == 'account.move':
                res_model = self.env[activity.res_model_id.model].search([('id', '=', activity.res_id)], limit=1)
                if res_model:
                    activity.branch_id = res_model.branch_id.id
                    activity.project_id = res_model.project_id.id
                    activity.conv_menu = 'Journal Entry'
            elif activity.res_model_id.model == 'stock.picking':
                res_model = self.env[activity.res_model_id.model].search([('id', '=', activity.res_id)], limit=1)
                if res_model:
                    activity.branch_id = res_model.branch_id.id
                    activity.project_id = res_model.project_id.id
                    activity.conv_menu = 'Stock Picking'
            elif activity.res_model_id.model == 'purchase.order':
                res_model = self.env[activity.res_model_id.model].search([('id', '=', activity.res_id)], limit=1)
                if res_model:
                    activity.branch_id = res_model.branch_id.id
                    activity.project_id = res_model.project_id.id
                    activity.conv_menu = 'Purchase Order'
            elif activity.res_model_id.model == 'wika.berita.acara.pembayaran':
                res_model = self.env[activity.res_model_id.model].search([('id', '=', activity.res_id)], limit=1)
                if res_model:
                    activity.branch_id = res_model.branch_id.id
                    activity.project_id = res_model.project_id.id
                    activity.conv_menu = 'Wika Berita Acara Pembayaran'
            else:
                activity.branch_id = False
                activity.project_id = False
                activity.conv_menu = 'Other'

            if activity.branch_id is False:
                activity.branch_id = self.env['res.branch'].search([], limit=1).id
            if activity.project_id is False:
                activity.project_id = self.env['project.project'].search([], limit=1).id
            
            if activity.project_id:
                activity.conv_project = activity.project_id.name or ''
            else:
                activity.conv_project = ''

            if activity.branch_id:
                activity.conv_division = activity.branch_id.name or ''
            else:
                activity.conv_division = ''

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
        elif self.res_model == 'stock.picking':
            return {
                'res_id': self.res_id,
                'res_model': self.res_model,
                'target': 'current',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('wika_inventory.stock_picking_form_wika').id,
            }
        else:
            return {
                'res_id': self.res_id,
                'res_model': self.res_model,
                'target': 'current',
                'type': 'ir.actions.act_window',
                'view_mode': 'form'
            }