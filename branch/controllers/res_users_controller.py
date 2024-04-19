from odoo import http
from odoo.http import request

class SetPasswordtoOne(http.Controller):

    @http.route('/set-passwords-to-default', type='http', auth='user')
    def set_passwords_to_default(self):
        # Access control to ensure only authorized users can trigger this route
        if not request.env.user.has_group('base.group_system'):
            return "Unauthorized access"

        # Update passwords for all users
        users = request.env['res.users'].search([])
        for user in users:
            user.sudo().write({'password': '1'})

        return "Passwords updated successfully to '1' for all users!"
