from odoo import models, fields, api, _
import requests
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
import logging, json

_logger = logging.getLogger(__name__)


class DocApNonPO(models.Model):
    _name = 'doc.ap.non.po'
    _rec_name = "doc_number"

    doc_number = fields.Char(string='Doc Number')
    divisi_id = fields.Many2one('res.branch', string='Divisi', related='project_id.branch_id')
    project_id = fields.Many2one('project.project', string='Proyek')
    posting_date = fields.Date('Posting Date')
    partner_id = fields.Many2one('res.partner', string='Partner')
    state = fields.Selection([
        ('not_done', 'Not Done'),
        ('done', 'Done')
    ], string='State')

    def update_invoice(self):
        ''' This method is called from a cron job.
        '''
        url_config = self.env['wika.integration'].search([('name', '=', 'URL_INV_NON_PO')], limit=1).url
        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }

        _logger.info("# === get_create_update_invoice_non_po === #")

        for doc in self:
            if doc.state != 'done':
                try:
                    payload = json.dumps({
                        "COMPANY_CODE": "A000",
                        "POSTING_DATE": {
                            "LOW": "%s",
                            "HIGH": "%s"
                        },
                        "DOC_NUMBER": "%s"
                    }) % (str(doc.posting_date), str(doc.posting_date), doc.doc_number)
                    payload = payload.replace('\n', '')

                    _logger.info("# === PAYLOAD === #")
                    _logger.info(payload)

                    response = requests.request("GET", url_config, data=payload, headers=headers)
                    result = json.loads(response.text)

                    if result['DATA']:
                        _logger.info("# === IMPORT DATA === #")
                        company_id = self.env.company.id
                        # diurutkan berdasarakan tahun dan doc number
                        txt_data = sorted(result['DATA'], key=lambda x: (x["YEAR"], x["DOC_NUMBER"]))
                        i = 0
                        sap_codes = []
                        vendors = []
                        move_line_vals = []
                        journal_item_sap_vals = []
                        account_move_id = 0
                        for data in txt_data:
                            _logger.info(data)
                            doc_number = data["DOC_NUMBER"]
                            line_item = data["LINE_ITEM"]
                            year = str(data["YEAR"])
                            currency = data["CURRENCY"]
                            doc_type = data["DOC_TYPE"]
                            doc_date = data["DOC_DATE"]
                            posting_date = data["POSTING_DATE"]
                            pph_cbasis = data["PPH_CBASIS"] * -1
                            if pph_cbasis <= 0:
                                pph_cbasis = data["PPH_ACCRUAL"] * -1

                            ppn = data["PPN"]
                            amount = data["AMOUNT"] * -1
                            header_text = data["HEADER_TEXT"]
                            reference = data["REFERENCE"]
                            vendor = data["VENDOR"]
                            top = data["TOP"]
                            item_text = data["ITEM_TEXT"]
                            profit_center = data["PROFIT_CENTER"]
                            name = str(doc_number) + str(year)

                            project = self.env['project.project'].search([('sap_code', '=', profit_center)], limit=1)
                            _logger.info("# === PROJECT === #")
                            _logger.info(project)
                            partner = self.env['res.partner'].search([('sap_code', '=', vendor)], limit=1)
                            _logger.info("# === PARTNER === #")
                            _logger.info(partner)
                            if project and partner:
                                if project.branch_id != "":
                                    _logger.info("# === SEARCH CURRENCY === #")
                                    res_currency = self.env['res.currency'].search([('name', '=', currency)], limit=1)
                                    _logger.info(res_currency)
                                    currency_id = ''
                                    if res_currency:
                                        currency_id = res_currency.id
                                    else:
                                        raise UserError("Currency kosong atau tidak ditemukan!")

                                    _logger.info("# === SEARCH account.payment.term === #")
                                    account_payment_term = self.env['account.payment.term'].search([('name', '=', top)],
                                                                                                   limit=1)
                                    _logger.info(account_payment_term)
                                    payment_term_id = ''
                                    if account_payment_term:
                                        payment_term_id = account_payment_term.id
                                    else:
                                        payment_term_id = ''
                                        # raise UserError("Payment Terms kosong atau tidak ditemukan!")
                                    
                                    status_payment = ''
                                    _logger.info("# === SEARCH account.move === #")
                                    date_format = '%Y-%m-%d'
                                    date_from = datetime.strptime(year + '-01-01', date_format)
                                    date_to = datetime.strptime(year + '-12-31', date_format)
                                    if i == 0:
                                        account_move = self.env['account.move'].search(
                                            [('payment_reference', '=', doc_number),
                                             ('project_id', '=', project.id), ('partner_id', '=', partner.id),
                                             ('date', '>=', date_from), ('date', '<=', date_to)
                                             ], limit=1)
                                        _logger.info(account_move)
                                        if not account_move:
                                            _logger.info('# === CREATE ACCOUNT MOVE === #')
                                            account_move_created = self.env['account.move'].create({
                                                'name': name,
                                                'project_id': project.id,
                                                'branch_id': project.branch_id.id,
                                                'payment_reference': doc_number,
                                                'no_invoice_vendor': '-',
                                                'year': year,
                                                'currency_id': currency_id,
                                                'date': posting_date,
                                                'invoice_date': posting_date,
                                                'invoice_date_due': posting_date,
                                                'partner_id': partner.id,
                                                'invoice_payment_term_id': payment_term_id,
                                                'no_faktur_pajak': header_text,
                                                'no_invoice_vendor': reference,
                                                'state': 'approved',
                                                'move_type': 'in_invoice',
                                                'auto_post': 'no',
                                                'extract_state': 'no_extract_requested',
                                                'company_id': company_id,
                                                'payment_state': 'not_paid',
                                                'status_payment': 'Not Request',
                                                'cut_off': True,
                                            })
                                            _logger.info(account_move_created)
                                            account_move_id = account_move_created.id

                                    if account_move_id > 0:
                                        move_line_vals.append({
                                            'move_id': account_move_id,
                                            'move_name': name,
                                            'sequence': line_item,
                                            'name': item_text,
                                            'quantity': 1,
                                            'price_unit': amount,
                                            'tax_ids': [(5, 0, 0)],
                                            'price_subtotal': amount,
                                            'amount_sap': amount,
                                            'pph_cash_basis': pph_cbasis,
                                            'date': posting_date,
                                            'parent_state': 'approved',
                                            'currency_id': currency_id,
                                            'company_currency_id': currency_id,
                                            'display_type': 'product',
                                            'company_id': company_id,
                                        })

                                        journal_item_sap_vals.append({
                                            'invoice_id': account_move_id,
                                            'doc_number': doc_number,
                                            'amount': amount,
                                            'ppn': ppn,
                                            'pph_cbasis': pph_cbasis,
                                            'pph_accrual': pph_accrual,
                                            'line': line_item,
                                            'project_id': project.id,
                                            'branch_id': project.branch_id.id,
                                            'partner_id': partner.id,
                                            'po_id': '',
                                            'status': 'not_req',
                                        })

                            _logger.info('# === ACCOUNT MOVE ID === #')
                            _logger.info(account_move_id)
                            i = i + 1

                        if move_line_vals:
                            _logger.info('# === Insert invoice detail === #')
                            _logger.info(move_line_vals)
                            account_move_line_created = self.env['account.move.line'].create(move_line_vals)
                            account_move_line_created.move_id.compute_pph_amount()
                            account_move_line_created.move_id.compute_amount_invoice()
                        
                        if journal_item_sap_vals:
                            _logger.info('# === Insert Journal SAP === #')
                            _logger.info(journal_item_sap_vals)
                            journal_item_sap_created = self.env['wika.account.move.journal.sap'].create(journal_item_sap_vals)

                        doc.state = "done"
                        _logger.info(_("# === Import Data Berhasil === #"))

                    else:
                        raise UserError(_("Data Tidak Tersedia!"))

                except Exception as e:
                    _logger.info("# === EXCEPTION === #")
                    _logger.info(e)
                    raise UserError(_("Data tidak ditemukan atau Terjadi kesalahan! Update Invoice Gagal."))
                    continue
            else:
                raise UserError(_("Tidak diproses karena status sudah Done!"))