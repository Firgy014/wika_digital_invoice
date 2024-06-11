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
import stat
import traceback
import logging
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
        _logger.warning("<<================== GENERATE AND BACKUP TXT DATA OF WDIGI TO REMOTE DIRECTORY ==================>>")
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

    def _generate_data_scf_cut(self):
        _logger.warning("<<================== GENERATE SCF TXT DATA OF WDIGI TO REMOTE DIRECTORY ==================>>")
        conf_ids = self.search([])
        for conf_id in conf_ids:
            try:
                N = 32
                today = datetime.now().strftime("%Y%m%d%H%M%S")
                res = ''.join(random.sample(string.ascii_uppercase + string.digits, k=N))
                dev_keys = ['YFII019', res, 'A000', 'AF00219I03', today]
                keys = ['NO', 'DOC_NUMBER', 'DOC_YEAR', 'POSTING_DATE', 'PERIOD', 'AMOUNT_SCF', 'WBS', 'ITEM_TEXT']
                query = helpers._get_computed_query_scf()

                self._cr.execute(query)
                vals = self.env.cr.fetchall()

                _logger.info(f"Fetched values: {vals}")
                if not vals:
                    _logger.warning("No data fetched from the database.")
                    continue

                buffer = StringIO()
                writer = csv.writer(buffer, delimiter='|')
                writer.writerow(dev_keys)
                writer.writerow(keys)

                for res in vals:
                    writer.writerow(res)

                buffer.flush()  # Explicitly flush the buffer

                out2 = buffer.getvalue().encode('utf-8')
                _logger.info(f"Buffer content: {buffer.getvalue()}")

                filename = 'YFII019_' + today + '.txt'
                file_path = os.path.join(conf_id.sftp_path, filename)
                _logger.info(f"File path: {file_path}")

                with open(file_path, 'wb') as fp:
                    fp.write(out2)
                    _logger.info('ISI NYA'+str(fp))
                    _logger.info("Data written to file successfully")



                # Change the file permissions
                os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # Equivalent to 0o777

                # Read and print the file content (emulating the cat command)
                with open(file_path, 'r') as fp:
                    file_content = fp.read()
                    print("File content:")
                    print(file_content)
                    _logger.info(f"File content:\n{file_content}")

                if conf_id.sftp_host:
                    _logger.info(file_path)
                    self._send_file_to_sftp(conf_id, file_path, filename)

            except Exception as e:
                _logger.error(f"Error occurred while generating and sending data: {str(e)}")
                _logger.error(traceback.format_exc())  # Log the stack trace for debugging

    def _generate_data_dp(self):
        _logger.warning("<<================== GENERATE INVOICE DP TXT DATA OF WDIGI TO REMOTE DIRECTORY ==================>>")
        conf_ids = self.search([])
        for conf_id in conf_ids:
            try:
                N = 32
                today = datetime.now().strftime("%Y%m%d%H%M%S")
                res = ''.join(random.sample(string.ascii_uppercase + string.digits, k=N))
                dev_keys = ['YFII020', res, 'A000', 'AF00219I03', today]
                keys = ['NO','DOC_DATE','POSTING_DATE','PERIOD','REFERENCE','HEADER_TXT','ACC_VENDOR','SPECIAL_GL','AMOUNT','TAX_CODE','DUE_ON','PO_NUMBER','PO_ITEM','PROFIT_CTR','TEXT']
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
                filename = ('YFII020_' + today + '.txt')

                file_path = os.path.join(conf_id.sftp_path, filename)
                with open(file_path, 'wb') as fp:
                    fp.write(out2)

                if conf_id.sftp_host:
                    self._send_file_to_sftp(conf_id, file_path, filename)

            except Exception as e:
                _logger.error(f"Error occurred while generating and sending data: {str(e)}")

    # def _send_file_to_sftp(self, conf_id, file_path, filename):
    #     try:
    #         _logger.info(f"Connecting to SFTP server: {conf_id.sftp_host}:{conf_id.sftp_port}")
    #         transport = paramiko.Transport((conf_id.sftp_host, conf_id.sftp_port))
    #         transport.connect(username=conf_id.sftp_user, password=conf_id.sftp_password)
    #         sftp = paramiko.SFTPClient.from_transport(transport)
    #         _logger.info("Connected to SFTP server successfully")

    #         _logger.info(f"Uploading file '{filename}' to SFTP server")
    #         sftp.put(file_path, os.path.join(conf_id.sftp_path, filename))
    #         _logger.info("File uploaded successfully")
    #     except Exception as e:
    #         _logger.error(f"Error occurred while sending file via SFTP: {str(e)}")
    #     finally:
    #         if 'sftp' in locals():
    #             sftp.close()
    #         if 'transport' in locals():
    #             transport.close()

    def _send_file_to_sftp(self, conf_id, file_path, filename):
        try:
            _logger.info(f"Connecting to SFTP server: {conf_id.sftp_host}:{conf_id.sftp_port}")
            transport = paramiko.Transport((conf_id.sftp_host, conf_id.sftp_port))
            transport.connect(username=conf_id.sftp_user, password=conf_id.sftp_password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            _logger.info("Connected to SFTP server successfully")

            remote_path = os.path.join(conf_id.sftp_path, filename)
            _logger.info(f"Uploading file '{filename}' to SFTP server at '{remote_path}'")
            sftp.put(file_path, remote_path)
            _logger.info("File uploaded successfully")

            # Verify the file content on the SFTP server (if possible)
            with sftp.open(remote_path, 'r') as remote_file:
                remote_content = remote_file.read()
                _logger.info(f"Remote file content:\n{remote_content}")

        except Exception as e:
            _logger.error(f"Error occurred while sending file via SFTP: {str(e)}")
            _logger.error(traceback.format_exc())  # Log the stack trace for debugging
        finally:
            if 'sftp' in locals():
                sftp.close()
            if 'transport' in locals():
                transport.close()


    def _update_invoice(self):
        invoice_model = self.env['account.move'].sudo()
        conf_model = self.env['sap.integration.configure'].sudo()

        conf_id = conf_model.search([('sftp_folder_archive', '!=', False)], limit=1)
        file_path = None
        if conf_id:
            outbound_dir = conf_id.sftp_folder
            file_name_prefix = 'YFII015A'
            for file_name in os.listdir(outbound_dir):
                if file_name.startswith(file_name_prefix):
                    file_path = os.path.join(outbound_dir, file_name)
                    break

        if not file_path:
            raise ValidationError(_("No file found with prefix {} in directory {}".format(file_name_prefix, outbound_dir)))

        updated_invoices = []
        try:
            with open(file_path, 'r') as file:
                print('TEST PATTTTHHHH', file_path)
                next(file)
                next(file)
                for line in file:
                    invoice_data = line.strip().split('|')
                    
                    if len(invoice_data) < 7:
                        _logger.error("Invalid invoice data format: %s", invoice_data)
                        continue
                    
                    no_inv = invoice_data[0]
                    invoice_id = invoice_model.search([('name', '=', no_inv)], limit=1)

                    if invoice_id:
                        update_vals = {
                            'invoice_number': invoice_data[1],
                            'year': invoice_data[2],
                            'dp_doc': invoice_data[4],
                            'retensi_doc': invoice_data[5],
                        }
                        
                        if invoice_data[6]:  # If AP_DOC exist
                            update_vals['payment_reference'] = invoice_data[6]
                            update_vals['no_doc_sap'] = invoice_data[3]
                            update_vals['dp_doc'] = invoice_data[4]
                            update_vals['retensi_doc'] = invoice_data[5]
                        else:  # If AP_DOC not exits
                            update_vals['payment_reference'] = invoice_data[3]
                            update_vals['no_doc_sap'] = ''
                        
                        invoice_id.write(update_vals)
                        updated_invoices.append(no_inv)
                    else:
                        _logger.warning("No matching invoice found for no_inv: %s", no_inv)

            shutil.move(file_path, os.path.join(conf_id.sftp_folder_archive, file_name))
            _logger.info("File moved to archive: %s", file_name)
        except FileNotFoundError:
            _logger.error("File not found: %s", file_path)
            raise ValidationError(_("File TXT dari SAP atas invoice yang dituju tidak ditemukan!"))
        except Exception as e:
            _logger.error("An error occurred: %s", str(e))
            raise ValidationError(_("An error occurred while updating invoices: %s" % str(e)))

        if updated_invoices:
            _logger.info("Successfully updated invoices: %s", updated_invoices)
        else:
            _logger.info("No invoices were updated.")

    def _update_payment_partial_request(self):
        partial_payment_request_model = self.env['wika.partial.payment.request'].sudo()
        conf_model = self.env['sap.integration.configure'].sudo()

        conf_id = conf_model.search([('sftp_folder_archive', '!=', False)], limit=1)
        if conf_id:
            outbound_dir = conf_id.sftp_folder
            file_name_prefix = 'YFII018A'
            _logger.info("# === UPDATE PARTIAL PAYMENT REQUEST === #" + file_name_prefix)
            _logger.info(outbound_dir)
            
            # try:
            # open an SSH connection
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(conf_id['sftp_host'], 22, conf_id['sftp_user'], conf_id['sftp_password'])
            # read the file using SFTP
            updated_ppr = []
            sftp = client.open_sftp()
            
            for file_name in sftp.listdir(outbound_dir):
                _logger.info("# === FILE NAME === #")
                _logger.info(file_name)
                if file_name.startswith(file_name_prefix):
                    file_path = os.path.join(outbound_dir, file_name)
                    _logger.info(file_path)
                    with sftp.open(file_path, 'r') as file:
                        next(file)  # Skip the header line
                        next(file)  # Skip the column titles
                        for line in file:
                            _logger.info("# === LINE === #" + line)
                            invoice_data = line.strip().split('|')
                            no_ppr = invoice_data[0]
                            _logger.info("# === SEARCH PARTIAL PAYMENT REQUEST === #")
                            ppr_ids = partial_payment_request_model.search([('no_doc_sap', '=', False), '|',
                                                                           ('name', '=', no_ppr),
                                                                           ('reference', '=', no_ppr)])
                            
                            _logger.info(ppr_ids)
                            if ppr_ids:
                                _logger.info("# === WRITE PARTIAL PAYMENT REQUEST === #")
                                for ppr_id in ppr_ids:
                                    ppr_id.write({
                                        'no_doc_sap': invoice_data[2],
                                        'year': invoice_data[3]
                                    })
                                    if ppr_id.invoice_id:
                                        ppr_id.invoice_id.write({
                                            'payment_reference': invoice_data[2]
                                        })

                                    updated_ppr.append(no_ppr)
                            
                    
                        # _logger.info(file_path)
                        # _logger.info(os.path.join(conf_id.sftp_folder_archive, file_name))
                        try:
                            sftp.remove(os.path.join(conf_id.sftp_folder_archive, file_name))
                        except OSError:
                            _logger.info("%s could not be deleted\n" % file_name)
                        
                        sftp.rename(file_path, os.path.join(conf_id.sftp_folder_archive, file_name))
            # close the connections
            sftp.close()
            client.close()
            _logger.info("# === UPDATE PARTIAL PAYMENT REQUEST SUCCESS === #")
            # except FileNotFoundError:
            #     pass
                # raise ValidationError(_("File TXT dari SAP atas invoice yang dituju tidak ditemukan!"))

    def _update_scf_invoice(self):
        invoice_model = self.env['account.move'].sudo()
        conf_model = self.env['sap.integration.configure'].sudo()

        conf_id = conf_model.search([('sftp_folder_archive', '!=', False)], limit=1)
        file_path = None
        if conf_id:
            outbound_dir = conf_id.sftp_folder
            file_name_prefix = 'YFII019'
            for file_name in os.listdir(outbound_dir):
                if file_name.startswith(file_name_prefix):
                    file_path = os.path.join(outbound_dir, file_name)
                    break

        if file_path:
            _logger.info("File path found: %s", file_path)
            updated_invoices = []
            try:
                with open(file_path, 'r') as file_txt:
                    next(file_txt)
                    next(file_txt)
                    for line in file_txt:
                        invoice_data = line.strip().split('|')
                        _logger.debug("Invoice data parsed: %s", invoice_data)
                        
                        if len(invoice_data) < 3:
                            _logger.error("Invalid invoice data format: %s", invoice_data)
                            continue

                        dig_code = invoice_data[0]
                        invoice_number = invoice_data[1]
                        year = invoice_data[2]

                        invoice_id = invoice_model.search([
                            ('name', '=', dig_code)
                            # ('is_mp_approved', '=', True)
                        ], limit=1)

                        if invoice_id:
                            update_vals = {
                                'name': dig_code,
                                'payment_reference': invoice_number,
                                'year': year,
                            }

                            invoice_id.write(update_vals)
                            updated_invoices.append(dig_code)
                            _logger.info("Successfully updated invoice: %s", dig_code)
                        else:
                            _logger.warning("No matching invoice found for DIG_CODE: %s", dig_code)
                            
                shutil.copy(file_path, os.path.join(conf_id.sftp_folder_archive, file_name))
                _logger.info("File copied to archive: %s", file_name)
            except FileNotFoundError:
                _logger.error("File not found: %s", file_path)
            except Exception as e:
                _logger.error("An error occurred: %s", str(e))
        else:
            _logger.error("No file found with prefix %s in directory %s", file_name_prefix, outbound_dir)

    def _update_dp_request_invoice(self):
        invoice_model = self.env['account.move'].sudo()
        conf_model = self.env['sap.integration.configure'].sudo()

        conf_id = conf_model.search([('sftp_folder_archive', '!=', False)], limit=1)
        file_path = None
        if conf_id:
            outbound_dir = conf_id.sftp_folder
            file_name_prefix = 'YFII020'
            for file_name in os.listdir(outbound_dir):
                if file_name.startswith(file_name_prefix):
                    file_path = os.path.join(outbound_dir, file_name)
                    break

        if not file_path:
            raise ValidationError(_("No file found with prefix {} in directory {}".format(file_name_prefix, outbound_dir)))

        updated_invoices = []
        try:
            with open(file_path, 'r') as file:
                next(file)
                next(file)
                for line in file:
                    invoice_data = line.strip().split('|')
                    
                    # if len(invoice_data) < 7:
                    #     _logger.error("Invalid invoice data format: %s", invoice_data)
                    #     continue
                    
                    dig_code = invoice_data[0]
                    belnr = invoice_data[1]
                    gjahr = invoice_data[2]

                    invoice_id = invoice_model.search([('name', '=', dig_code)], limit=1)

                    if invoice_id:
                        update_vals = {
                            'name': dig_code,
                            'payment_reference': belnr,
                            'year': gjahr
                        }
                        
                        invoice_id.write(update_vals)
                        updated_invoices.append(dig_code)
                    else:
                        _logger.warning("No matching invoice found for no_inv: %s", dig_code)

            shutil.move(file_path, os.path.join(conf_id.sftp_folder_archive, file_name))
            _logger.info("File moved to archive: %s", file_name)
        except FileNotFoundError:
            _logger.error("File not found: %s", file_path)
            raise ValidationError(_("File TXT dari SAP atas invoice yang dituju tidak ditemukan!"))
        except Exception as e:
            _logger.error("An error occurred: %s", str(e))
            raise ValidationError(_("An error occurred while updating invoices: %s" % str(e)))

        if updated_invoices:
            _logger.info("Successfully updated invoices: %s", updated_invoices)
        else:
            _logger.info("No invoices were updated.")
        
