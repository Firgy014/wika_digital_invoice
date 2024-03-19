from odoo import fields, models, _
import logging

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


