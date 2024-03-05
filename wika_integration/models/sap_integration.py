from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging
import random
import string
from . import helpers

import io
_logger = logging.getLogger(__name__)
try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')

from io import StringIO

class SAPIntegration(models.Model):
    _name = 'wika.sap.integration'
    _description = 'SAP Integration'

    files = fields.Binary(string="Import File")
    datas_fname = fields.Char(string='Import File Name')
    file_opt = fields.Selection([
        ('excel', 'Excel'),
        ('txt', 'TXT')
    ], default='txt', string='File Option')
    type = fields.Selection([
        ('upload', 'Upload'),
        ('generate', 'Generate')
    ], default='generate', string='Type')
    form = fields.Selection([
        ('ncl', 'NCL'),
        ('vendor_bills', 'Vendor Bills'),
        ('payroll', 'Payroll')
    ], string='Form')
    pelunasan = fields.Boolean(string='Pelunasan', default=False)
    file_template = fields.Binary(string = 'Export File', readonly=True)

    def journal_item(self):
        raise ValidationError(_('Journal Item method is triggered'))

    def import_payroll(self):
        raise ValidationError(_('Import Payroll method is triggered'))

    def import_pelunasan(self):
        raise ValidationError(_('Import Pelunasan method is triggered'))

    def generate_data(self):
        raise ValidationError(_('Generate Data method is triggered'))

    def generate_data_vendor_bills(self):
        N = 32
        today = datetime.now().strftime("%Y%m%d%H%M%S")
        if self.type == 'generate' and self.form == 'vendor_bills':
            res = ''.join(random.sample(string.ascii_uppercase + string.digits, k=N))
            dev_keys = ['YFII006', res,'A000','',today]
            keys = ['DOC_DATE', 'PSTNG_DATE', 'REF_DOC_NO', 'GROSS_AMOUNT', 'BLINE_DATE', 'HEADER_TXT',
                    'ITEM_TEXT', 'HKONT', 'RETENTION_DUE_DATE', 'TAX_BASE_AMOUNT', 'WI_TAX_TYPE', 'WI_TAX_CODE',
                    'WI_TAX_BASE', 'PO_NUMBER', 'PO_ITEM', 'REF_DOC', 'REF_DOC_YEAR', 'REF_DOC_IT', 'ITEM_AMOUNT',
                    'QUANTITY', 'SHEET_NO']
            
            query = helpers._get_computed_query()

        buffer = StringIO()
        writer = csv.writer(buffer, delimiter='|')
        self._cr.execute(query)
        vals = self._cr.fetchall()
        writer.writerow(dev_keys)
        writer.writerow(keys)
        for res in vals:
            writer.writerow(res)
        out2 = (buffer.getvalue()).encode('utf-8')
        gentextfile = base64.b64encode(out2)
        filename = ('YFII006_' + today + '.txt')

        self.write({'file_template': gentextfile,'datas_fname':filename})

        form_id = self.env.ref('wika_integration.template_sap_integration_form_view')
        return {
            'name': 'Generate & Download File',
            'res_model': 'wika.sap.integration',
            'view_id': False,
            'res_id': self.id,
            'views': [(form_id.id, 'form')],
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }