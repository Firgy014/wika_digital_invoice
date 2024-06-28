from odoo import models, fields, _
import logging
from datetime import datetime
import random
import string
import os
from . import helpers
from io import StringIO

_logger = logging.getLogger(__name__)
try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')

class PaymentRequestInherit(models.Model):
    _inherit = 'wika.payment.request'

    is_sent_to_sap = fields.Boolean(string='Generated and Sent to SAP', default=False, store=True)

    def send_reclass_ppn_waba(self):
        _logger.warning("<<================== GENERATE REQUESTED WABA INVOICE TXT DATA OF WDIGI TO REMOTE DIRECTORY ==================>>")
        # active_id = self.env.context.get('active_id')
        active_id = self.id
        if active_id:
            payment_id = self.sudo().browse([active_id])
            conf_ids = self.env['sap.integration.configure'].sudo().search([])
            for conf_id in conf_ids:
                try:
                    N = 32
                    today = datetime.now().strftime("%Y%m%d%H%M%S")
                    res = ''.join(random.sample(string.ascii_uppercase + string.digits, k=N))
                    dev_keys = ['YFII026', res, 'JAB0', 'AF00219I03', today]
                    keys = ['NO','DOC_NUMBER','DOC_YEAR','POSTING_DATE','PERIOD']
                
                    query = helpers._get_computed_query_reclass_ppn_waba(payment_id)

                    self._cr.execute(query)
                    vals = self.env.cr.fetchall()

                    buffer = StringIO()
                    writer = csv.writer(buffer, delimiter='|')
                    writer.writerow(dev_keys)
                    writer.writerow(keys)

                    for res in vals:
                        writer.writerow(res)

                    out2 = buffer.getvalue().encode('utf-8')
                    filename = ('YFII026_' + today + '.txt')

                    file_path = os.path.join(conf_id.sftp_path, filename)
                    with open(file_path, 'wb') as fp:
                        fp.write(out2)

                    # payment_id.write({'is_sent_to_sap':True})

                except Exception as e:
                    _logger.error(f"Error occurred while generating and sending data: {str(e)}")