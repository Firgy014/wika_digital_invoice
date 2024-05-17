from odoo import http
import requests, json
from datetime import datetime
from odoo.http import request, _logger, Response
from werkzeug.utils import redirect

class checkUser(http.Controller):
    @http.route('/my/route', auth='user', website=True)
    def check_user_login(self, **kw):
        user = http.request.env.user
        print("CHECK USERS", user)
        return http.request.render('ademord_dashboard.ChartRenderer', {
            'user_level': user.level
        })
