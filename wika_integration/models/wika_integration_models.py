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
    request_ids = fields.One2many(comodel_name='wika.integration.line',inverse_name='integration_id')
    api_user = fields.Char(string='API User')
    api_pword = fields.Char(string='API Password')

class wika_integration_line(models.Model):
    _name = 'wika.integration.line'
    _description='Wika Integration.line'

    integration_id  = fields.Many2one(comodel_name='wika.integration')
    request= fields.Text(string='Request')
    request_date= fields.Datetime(string='Request Date')
    response = fields.Text(string='Response')