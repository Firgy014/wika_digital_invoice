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
        ('vendor_bills_scf', 'Vendor Bills with SCF'),
        ('vendor_bills_dp', 'Vendor Bills with DP'),
        ('payroll', 'Payroll'),
        ('partial_payment', 'Partial Payment')
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
            dev_keys = ['YFII015', res,'A000','AD00118N05',today]
            keys = ['NO','DOC_DATE', 'PSTNG_DATE', 'REF_DOC_NO', 'GROSS_AMOUNT', 'BLINE_DATE', 'HEADER_TXT',
                    'ITEM_TEXT', 'HKONT', 'TAX_BASE_AMOUNT', 'WI_TAX_TYPE', 'WI_TAX_CODE', 'WI_TAX_BASE',
                    'PO_NUMBER', 'PO_ITEM', 'REF_DOC', 'REF_DOC_YEAR', 'REF_DOC_IT', 'ITEM_AMOUNT',
                    'QUANTITY', 'SHEET_NO', 'RETENTION_DUE_DATE','IND_DP','DP_AMOUNT']
            
            query = helpers._get_computed_query()

        self._cr.execute(query)
        vals = self.env.cr.fetchall()

        # unique_move_ids = set(val[0] for val in vals)
        # for move_id in unique_move_ids:
        #     move = self.env['account.move'].browse(move_id)
        #     move.write({'is_generated': True})

        buffer = StringIO()
        writer = csv.writer(buffer, delimiter='|')

        writer.writerow(dev_keys)
        writer.writerow(keys)

        for res in vals:
            writer.writerow(res)

        out2 = (buffer.getvalue()).encode('utf-8')
        gentextfile = base64.b64encode(out2)
        filename = ('YFII015_' + today + '.txt')

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
    
    def generate_data_vendor_bills_scf(self):
        N = 32
        today = datetime.now().strftime("%Y%m%d%H%M%S")
        if self.type == 'generate' and self.form == 'vendor_bills_scf':
            res = ''.join(random.sample(string.ascii_uppercase + string.digits, k=N))
            dev_keys = ['YFII019', res, 'A000', 'AF00219I03', today]
            keys = ['NO', 'DOC_NUMBER', 'DOC_YEAR', 'POSTING_DATE', 'PERIOD', 'AMOUNT_SCF', 'WBS', 'ITEM_TEXT']
            query = helpers._get_computed_query_scf()

        self._cr.execute(query)
        vals = self.env.cr.fetchall()

        # _logger.info(f"Fetched values: {vals}")
        # if not vals:
        #     _logger.warning("No data fetched from the database.")
        #     continue

        buffer = StringIO()
        writer = csv.writer(buffer, delimiter='|')

        writer.writerow(dev_keys)
        writer.writerow(keys)

        for res in vals:
            writer.writerow(res)

        out2 = buffer.getvalue().encode('utf-8')
        gentextfile = base64.b64encode(out2)
        filename = 'YFII019_' + today + '.txt'

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
    
    def generate_data_vendor_bills_dp(self):
        N = 32
        today = datetime.now().strftime("%Y%m%d%H%M%S")
        if self.type == 'generate' and self.form == 'vendor_bills_dp':
            res = ''.join(random.sample(string.ascii_uppercase + string.digits, k=N))
            dev_keys = ['YFII020', res, 'A000', 'AF00219I03', today]
            keys = ['NO','DOC_DATE','POSTING_DATE','PERIOD','CURRENCY','REFERENCE','HEADER_TXT',
                    'ACC_VENDOR','SPECIAL_GL','AMOUNT','TAX_CODE','DUE_ON','PO_NUMBER','PO_ITEM',
                    'PROFIT_CTR','TEXT','WHT_TYPE','WHT_CODE']
            query = helpers._get_computed_query_dp()

        self._cr.execute(query)
        vals = self.env.cr.fetchall()

        buffer = StringIO()
        writer = csv.writer(buffer, delimiter='|')

        writer.writerow(dev_keys)
        writer.writerow(keys)

        for res in vals:
            writer.writerow(res)

        out2 = buffer.getvalue().encode('utf-8')
        gentextfile = base64.b64encode(out2)
        filename = 'YFII020_' + today + '.txt'

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
    
    
    def generate_data_partial_payment(self):
        N = 32
        today = datetime.now().strftime("%Y%m%d%H%M%S")
        if self.type == 'generate' and self.form == 'partial_payment':
            res = ''.join(random.sample(string.ascii_uppercase + string.digits, k=N))
            dev_keys = ['YFII018', res,'A000','AF00219I03',today]
            keys = ['NO','DOC_NUMBER','DOC_YEAR', 'POSTING_DATE', 'PERIOD', 'AMOUNT1', 'AMOUNT2']
            
            query = helpers._get_computed_partial_payment_query()

        self._cr.execute(query)
        vals = self.env.cr.fetchall()

        # unique_move_ids = set(val[0] for val in vals)
        # for move_id in unique_move_ids:
        #     move = self.env['account.move'].browse(move_id)
        #     move.write({'is_generated': True})

        buffer = StringIO()
        writer = csv.writer(buffer, delimiter='|')

        writer.writerow(dev_keys)
        writer.writerow(keys)

        for res in vals:
            writer.writerow(res)

        out2 = (buffer.getvalue()).encode('utf-8')
        gentextfile = base64.b64encode(out2)
        filename = ('YFII018_' + today + '.txt')

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