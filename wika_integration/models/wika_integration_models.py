# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError, Warning
import logging, json
_logger = logging.getLogger(__name__)

class wika_integration(models.Model):
    _name = 'wika.integration'
    _description='Wika Integration'

    name = fields.Char(string="nama")
    app = fields.Selection(string="Application",
                           selection=[
                               ('PMCS', 'PMCS'),
                               ('SIMDIV', 'SIMDIV'),
                               ('SCM', 'SCM'),
                               ('SAP', 'SAP'),
                               ('CRM', 'CRM'),
                               ('WZONE', 'WZONE'),
                               ('HC', 'HC')])
    app_secret = fields.Char(string="Secret Key Application")
    url = fields.Char(string="URL")
    payload = fields.Text(string="Payload")
    _sql_constraints = [
        ('app_name_unique', 'unique (name)', 'Nama harus unik!')
    ]



    def tag_coa(self):
        coa = self.env['account.account'].search([('company_id','=',1)])
        for c in coa:
            coa_lain = self.env['account.account'].search([('code', '=', c.code), ('company_id', '!=', 1)])
            for cc in coa_lain:
                cc.tag_ids = c.tag_ids


