from odoo import fields, models, _
from odoo.exceptions import ValidationError
import logging
from datetime import datetime
import logging
import random
import string
import json
from . import helpers
import os
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
import shutil
try:
    import paramiko
except ImportError:
    raise ImportError(
        'This module needs paramiko to automatically write backups to the FTP through SFTP. Please install paramiko on your system. (sudo pip3 install paramiko)')


_logger = logging.getLogger(__name__)

class sap_integration_configure(models.Model):
    _name = 'sap.integration.configure'
    _description = 'SAP Integration Configuration Record'
    _rec_name='sftp_path'

    folder = fields.Char('Backup Directory', help='Absolute path for storing the backups', required='True', default='/odoo/backups')
    sftp_folder = fields.Char('SFTP Directory Outbound', help='Absolute path for storing the backups', required='True')
    sftp_folder_archive = fields.Char('SFTP Archive Outbound', help='Absolute path for storing the backups', required='True')
    sftp_folder_success= fields.Char('SFTP Success Outbound', help='Absolute path for storing the backups', required='True')
    sftp_folder_error= fields.Char('SFTP Error Outbound', help='Absolute path for storing the backups', required='True')

    sftp_path = fields.Char('Inbound external server', help='The location to the folder where the dumps should be written to. For example /odoo/backups/.\nFiles will then be written to /odoo/backups/ on your remote server.')
    sftp_host = fields.Char('IP Address SFTP Server', help='The IP address from your remote server. For example 192.168.0.1')
    sftp_port = fields.Integer('SFTP Port', help='The port on the FTP server that accepts SSH/SFTP calls.', default=22)
    sftp_user = fields.Char('Username SFTP Server', help='The username where the SFTP connection should be made with. This is the user on the external server.')
    sftp_password = fields.Char('Password User SFTP Server', help='The password from the user where the SFTP connection should be made with. This is the password from the user on the external server.')

    active = fields.Boolean('Active')

    def test_sftp_connection(self, context=None):
        self.ensure_one()

        # Check if there is a success or fail and write messages
        messageTitle = ""
        messageContent = ""
        error = ""
        has_failed = False

        for rec in self:
            pathToWriteTo = rec.sftp_path
            print("pathToWriteTo", pathToWriteTo)
            ipHost = rec.sftp_host
            portHost = rec.sftp_port
            usernameLogin = rec.sftp_user
            passwordLogin = rec.sftp_password

            # Initialize the variable 's' to None
            s = None

            # Connect with external server over SFTP, so we know sure that everything works.
            try:
                # masuk_test_sftp_bismillah
                s = paramiko.SSHClient()
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                s.connect(ipHost, portHost, usernameLogin, passwordLogin, timeout=10)
                sftp = s.open_sftp()
                messageTitle = _("Connection Test Succeeded!\nEverything seems properly set up for FTP back-ups!")
            except Exception as e:
                _logger.critical('There was a problem connecting to the remote ftp: ' + str(e))
                error += str(e)
                has_failed = True
                messageTitle = _("Connection Test Failed!")
                if len(rec.sftp_host) < 8:
                    messageContent += "\nYour IP address seems to be too short.\n"
                messageContent += _("Here is what we got instead:\n")
            finally:
                if s is not None:
                    s.close()

        if has_failed:
            raise Warning(messageTitle + '\n\n' + messageContent + "%s" % str(error))
        else:
            raise Warning(messageTitle + '\n\n' + messageContent)

    def _generate_data(self):
        _logger.warning("<<================== GENERATE AND BACKUP TXT DATA OF WDIGI TO DIRECTORY ==================>>")
        conf_ids = self.search([])
        for conf_id in conf_ids:
            try:
                N = 32
                today = datetime.now().strftime("%Y%m%d%H%M%S")
                res = ''.join(random.sample(string.ascii_uppercase + string.digits, k=N))
                dev_keys = ['YFII015', res, 'A000', 'AD00118N05', today]
                keys = ['NO','DOC_DATE', 'PSTNG_DATE', 'REF_DOC_NO', 'GROSS_AMOUNT', 'BLINE_DATE', 'HEADER_TXT',
                        'ITEM_TEXT', 'HKONT', 'TAX_BASE_AMOUNT', 'WI_TAX_TYPE', 'WI_TAX_CODE', 'WI_TAX_BASE',
                        'PO_NUMBER', 'PO_ITEM', 'REF_DOC', 'REF_DOC_YEAR', 'REF_DOC_IT', 'ITEM_AMOUNT',
                        'QUANTITY', 'SHEET_NO', 'RETENTION_DUE_DATE']

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

                out2 = buffer.getvalue().encode('utf-8')
                filename = ('YFII015_' + today + '.txt')

                file_path = os.path.join(conf_id.sftp_path, filename)
                print("====file_path", file_path)
                with open(file_path, 'wb') as fp:
                    fp.write(out2)

                if conf_id.sftp_host:
                    self._send_file_to_sftp(conf_id, file_path, filename)
            except Exception as e:
                _logger.error(f"Error occurred while generating and sending data: {str(e)}")

    def _send_file_to_sftp(self, conf_id, file_path, filename):
        try:
            _logger.info(f"Connecting to SFTP server: {conf_id.sftp_host}:{conf_id.sftp_port}")
            transport = paramiko.Transport((conf_id.sftp_host, conf_id.sftp_port))
            transport.connect(username=conf_id.sftp_user, password=conf_id.sftp_password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            _logger.info("Connected to SFTP server successfully")

            _logger.info(f"Uploading file '{filename}' to SFTP server")
            sftp.put(file_path, os.path.join(conf_id.sftp_path, filename))
            _logger.info("File uploaded successfully")
        except Exception as e:
            _logger.error(f"Error occurred while sending file via SFTP: {str(e)}")
        finally:
            if 'sftp' in locals():
                sftp.close()
            if 'transport' in locals():
                transport.close()

    # def _update_invoice(self):
    #     import os
    #     import shutil
        
    #     invoice_model = self.env['account.move'].sudo()
    #     conf_model = self.env['sap.integration.configure'].sudo()

    #     conf_id = conf_model.search([('sftp_folder_archive', '!=', False)], limit=1)
    #     if conf_id:
    #         outbound_dir = conf_id.sftp_folder
    #         file_name_prefix = 'YFII015A'
    #         for file_name in os.listdir(outbound_dir):
    #             if file_name.startswith(file_name_prefix):
    #                 file_path = os.path.join(outbound_dir, file_name)

    #     updated_invoices = []
    #     try:
    #         with open(file_path, 'r') as file_txt:
    #             next(file_txt)  # Skip the header line
    #             next(file_txt)  # Skip the column titles
    #             for line in file_txt:
    #                 invoice_data = line.strip().split('|')
    #                 print("invoice_data", invoice_data)
    #                 no_inv = invoice_data[0]
    #                 print('noinnnnnv',no_inv)
    #                 invoice_id = invoice_model.search([
    #                     ('name', '=', no_inv),
    #                     ('is_mp_approved', '=', True),
    #                     ('invoice_number', '=', False)
    #                 ], limit=1)
    #                 if invoice_id:
    #                     update_vals = {
    #                         'invoice_number': invoice_data[3],  # ACC_DOC
    #                         'year': invoice_data[2],  # GJAHR
    #                         'dp_doc': invoice_data[4],  # DP_DOC
    #                         'retensi_doc': invoice_data[5],  # RET_DOC
    #                     }
    #                     if invoice_data[6]:  # AP_DOC
    #                         print("ada")
    #                         update_vals.update({
    #                             'payment_reference': invoice_data[6],
    #                             'no_doc_sap': invoice_data[1]  # BELNR
    #                         })
    #                     else:
    #                         print("gaada")
    #                         update_vals['payment_reference'] = invoice_data[1]  # BELNR

    #                     invoice_id.write(update_vals)
    #                     updated_invoices.append(no_inv)
    #                 else:
    #                     pass
    #             shutil.move(file_path, os.path.join(conf_id.sftp_folder_archive, file_name))
    #     except FileNotFoundError:
    #         pass
    #     print('ALHAMDULILLAH')
    #         #raise ValidationError(_("File TXT dari SAP atas invoice yang dituju tidak ditemukan!"))

    def _update_invoice(self):
        invoice_model = self.env['account.move'].sudo()
        conf_model = self.env['sap.integration.configure'].sudo()

        conf_id = conf_model.search([('sftp_folder_archive', '!=', False)], limit=1)
        if conf_id:
            outbound_dir = conf_id.sftp_folder
            file_name_prefix = 'YFII015A'
            for file_name in os.listdir(outbound_dir):
                if file_name.startswith(file_name_prefix):
                    file_path = os.path.join(outbound_dir, file_name)

        updated_invoices = []
        try:
            with open(file_path, 'r') as file_txt:
                next(file_txt)  # Skip the header line
                next(file_txt)  # Skip the column titles
                for line in file_txt:
                    invoice_data = line.strip().split('|')
                    print("invoice_data", invoice_data)
                    acc_doc = invoice_data[3]  # ACC_DOC
                    invoice_id = invoice_model.search([
                        ('name', '=', acc_doc),
                        ('is_mp_approved', '=', True),
                        ('invoice_number', '=', False)
                    ], limit=1)
                    if invoice_id:
                        update_vals = {
                            'name': acc_doc,
                            'year': invoice_data[2],  # GJAHR
                            'dp_doc': invoice_data[4],  # DP_DOC
                            'retensi_doc': invoice_data[5],  # RET_DOC
                        }
                        if invoice_data[6]:  # AP_DOC
                            update_vals.update({
                                'payment_reference': invoice_data[6],
                                'no_doc_sap': invoice_data[1]  # BELNR
                            })
                        else:
                            update_vals['payment_reference'] = invoice_data[1]  # BELNR

                        invoice_id.write(update_vals)
                        updated_invoices.append(acc_doc)
                    else:
                        pass
                shutil.move(file_path, os.path.join(conf_id.sftp_folder_archive, file_name))
        except FileNotFoundError:
            pass

