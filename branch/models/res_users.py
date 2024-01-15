from odoo import api, fields, models, _


class res_users(models.Model):
    _inherit = 'res.users'

    branch_id = fields.Many2one('res.branch', 'Divisi')
    branch_ids = fields.Many2many('res.branch', 'user_id', 'branch_id', string='Multi Divisi')
    project_id = fields.Many2one('project.project', string='Project')


    def write(self, values):
        if 'branch_id' in values or 'branch_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()
            # self.has_group.clear_cache(self)
        user = super(res_users, self).write(values)
        return user
