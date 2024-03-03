from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging
import random
import string

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
    ], default='Upload', string='Type')
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
        if self.type == 'Generate' and self.form == 'Vendor Bills':
            res = ''.join(random.sample(string.ascii_uppercase + string.digits, k=N))
            dev_keys = ['YFII006', res,'A000','',today]
            keys = ['DOC_DATE', 'PSTNG_DATE', 'REF_DOC_NO', 'GROSS_AMOUNT', 'BLINE_DATE', 'HEADER_TXT',
                    'ITEM_TEXT', 'HKONT', 'RETENTION_DUE_DATE', 'TAX_BASE_AMOUNT', 'WI_TAX_TYPE', 'WI_TAX_CODE',
                    'WI_TAX_BASE', 'PO_NUMBER', 'PO_ITEM', 'REF_DOC', 'REF_DOC_YEAR', 'REF_DOC_IT', 'ITEM_AMOUNT',
                    'QUANTITY', 'SHEET_NO']
            
            # keyssss = ['DOC_NO','BUS_ACT','DOC_STATUS','USERNAME','COMP_CODE','DOC_TYPE','PSTNG_DATE','DOC_DATE','REF_DOC_NO','HEADER_TXT','FISC_YEAR','FIS_PERIOD',
            #         'ITEMNO_ACC','GL_ACCOUNT','ITEM_TEXT','TAX_CODE','COSTCENTER','ORDERID','ITEMNO_ACC_PAY','GL_ACCOUNT_PAY','VENDOR_NO','PMNTTRMS','BLINE_DATE','PYMT_METH',
            #         'ITEM_TEXT_PAY','ITEMNO_ACC_CURR','CURRENCY','AMT_DOCCUR']

            query = """
SELECT
		to_char(inv.date_invoice, 'yyyymmdd') as DOC_DATE,
		to_char(inv.date_invoice, 'yyyymmdd') as PSTNG_DATE,
		'2' as REF_DOC_NO,
		'WIKA_INT' as GROSS_AMOUNT,
		'A000' as BLINE_DATE,
		'KR' as HEADER_TXT,
		to_char(inv.date_invoice, 'yyyymmdd') as ITEM_TEXT,
		to_char(inv.date_invoice, 'yyyymmdd') as HKONT,
		inv.reference as RETENTION_DUE_DATE,
		inv.reference as TAX_BASE_AMOUNT,
		to_char(inv.date_invoice, 'yyyy') as WI_TAX_TYPE,
		to_char(inv.date_invoice, 'mm') as WI_TAX_CODE,
		ROW_NUMBER () OVER  (partition by inv.id order by line.id asc)::text as WI_TAX_BASE,
		coa.sap_code as PO_NUMBER,
		line.name as PO_ITEM,
		'V1' as REF_DOC,
		branch.sap_code_cost as REF_DOC_YEAR,
		'' as REF_DOC_IT,
		'' as ITEM_AMOUNT,
		'' as QUANTITY,
		'' as SHEET_NO,

		'' as PMNTTRMS,
		'' as BLINE_DATE,
		''  as PYMT_METH,
		'' as ITEM_TEXT_PAY,		
		ROW_NUMBER () OVER  (partition by inv.id order by line.id asc)::text as ITEMNO_ACC_CURR,
		'IDR' as CURRENCY,
		line.price_subtotal as AMT_DOCCUR
FROM account_move inv
FROM join account_invoice_line line on line.invoice_id=inv."id"
FROM join res_branch branch on branch.id=inv.branch_id
FROM join account_account coa on coa.id=line.account_id
FROM join res_partner partner on partner.id=inv.partner_id
WHERE inv.send='t' 


 UNION ALL
 SELECT 
		inv.id as  DOC_NO,
		 'RVBP' as BUS_ACT,
		 '2' as DOC_STATUS,
		'WIKA_INT' as USERNAME,
		'A000' as COMP_CODE,
		'KR' as DOC_TYPE,
		 to_char(inv.date_invoice, 'yyyymmdd') as PSTNG_DATE,
		to_char(inv.date_invoice, 'yyyymmdd') as DOC_DATE,
		inv.reference as REF_DOC_NO,
		inv.reference as HEADER_TXT,
		to_char(inv.date_invoice, 'yyyy') as FISC_YEAR,
		to_char(inv.date_invoice, 'mm') as FIS_PERIOD,
		''  as ITEMNO_ACC,
		'' as GL_ACCOUNT,
		'' as ITEM_TEXT,
		'' as TAX_CODE,
		'' as COSTCENTER,
		'' as ORDERID,
		(count(line.id)+1)::text as ITEMNO_ACC_PAY,
		partner.sap_code as VENDOR_NO,
		coa.sap_code as GL_ACCOUNT,
		'ZC01' as PMNTTRMS,
		 to_char(inv.date_invoice, 'yyyymmdd') as BLINE_DATE,
		 'F'  as PYMT_METH,
		 inv.reference as ITEM_TEXT_PAY,
		(count(line.id)+1)::text as ITEMNO_ACC,
		'IDR' as CURRENCY,
		-sum(line.price_subtotal) as AMT_DOCCUR
FROM account_invoice inv
FROM join account_invoice_line line on line.invoice_id=inv."id"
FROM join res_branch branch on branch.id=inv.branch_id
FROM join account_account coa on coa.id=inv.account_id
FROM join res_partner partner on partner.id=inv.partner_id
WHERE inv.send='t' 
GROUP BY inv.id,partner.sap_code,coa.sap_code
ORDER BY DOC_NO
"""

        buffer = StringIO()
        writer = csv.writer(buffer, delimiter='|')
        self._cr.execute(query)
        vals = self._cr.fetchall()
        writer.writerow(dev_keys)
        writer.writerow(keys)
        for res in vals:
            writer.writerow(res)
        out2 = (buffer.getvalue()).encode('utf-8')
        print (out2)
        gentextfile = base64.b64encode(out2)
        print (type(gentextfile))
        filename = ('YFII006_'+today+'.txt')

        self.write({'file_template': gentextfile,'datas_fname':filename})

        form_id = self.env.ref('sap_integration.template_sap_integrationiew')
        return {
            'name': 'Download File',
            'res_model': 'sap.integration',
            'view_id': False,
            'res_id': self.id,
            'views': [(form_id.id, 'form')],
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }

