# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError, Warning,AccessError
import logging, json
_logger = logging.getLogger(__name__)

class wika_get_invoice_non_po(models.Model):
    _name = 'wika.get.invoice.non_po'
    _description='Wika Get Invoice Non PO'

    name = fields.Char(string="Doc Number")
    tgl_mulai = fields.Date(string="Tgl Mulai")
    tgl_akhir = fields.Date(string="Tgl Akhir")
    status=fields.Char(string='Status')

    def init(self):
        _logger.info("CREATING FUNCTION wika create update invoice non po...")
        self.env.cr.execute("""
            CREATE OR REPLACE FUNCTION "public"."wika_cu_inv_non_po"("v_data" TEXT)
            RETURNS "pg_catalog"."void" AS $BODY$ 
            DECLARE
                v_uid INTEGER;
                records TEXT[];
                rec TEXT;
                inv_rec TEXT[];
				project_rec TEXT[];
                v_doc_number TEXT; 
                v_line_item INTEGER; 
                v_year TEXT;
                v_currency TEXT;
                v_doc_type TEXT;
                v_doc_date DATE;
                v_posting_date DATE;
                v_pph_cbasis NUMERIC;
                v_amount NUMERIC;
                v_header_text TEXT;
                v_reference TEXT;
                v_vendor TEXT;
                v_top TEXT;
                v_item_text TEXT;
                v_profit_center TEXT;
				v_company_id INTEGER;
                v_payment_state TEXT;
                
                v_project_id INTEGER;
                v_branch_id INTEGER;
                v_vendor_id INTEGER;
                v_currency_id INTEGER;
                v_payment_term_id INTEGER;
                v_invoice_exist INTEGER;
                v_resource_id INTEGER;
                v_move_line_id INTEGER;

            BEGIN
                v_uid = 1;
                SELECT string_to_array(v_data, '|') INTO records;
                FOREACH rec IN ARRAY records LOOP
                    SELECT string_to_array(rec, '~~') INTO inv_rec;
                    v_doc_number = inv_rec[1];
                    v_line_item = inv_rec[2];
                    v_year = inv_rec[3];
                    v_currency = inv_rec[4];
                    v_doc_type = inv_rec[5];
                    v_doc_date = inv_rec[6];
                    v_posting_date = inv_rec[7];
                    v_pph_cbasis = inv_rec[8];
                    v_amount = inv_rec[9];
                    v_header_text = inv_rec[10];
                    v_reference = inv_rec[11];
                    v_vendor = trim(inv_rec[12]);
                    v_top = inv_rec[13];
                    v_item_text = inv_rec[14];
                    v_profit_center = trim(inv_rec[15]);
					v_company_id = trim(inv_rec[16]);
                    v_project_id = trim(inv_rec[17]);
                    v_branch_id = trim(inv_rec[18]);
                    v_vendor_id = trim(inv_rec[19]);
										
                    SELECT id FROM res_currency INTO v_currency_id WHERE name = v_currency;
                    -- RAISE NOTICE 'v_currency_id %', v_currency_id;
                    SELECT id FROM account_payment_term WHERE name::text LIKE '%v_top%' INTO v_payment_term_id;
                    -- RAISE NOTICE 'v_payment_term_id %', v_payment_term_id;
                    v_payment_state = '';
                    SELECT id, payment_state FROM account_move
                        WHERE payment_reference = v_doc_number AND year = v_year 
                        AND project_id = v_project_id AND partner_id = v_vendor_id
                        INTO v_invoice_exist, v_payment_state;
                    
                    -- RAISE NOTICE 'v_invoice_exist %', v_invoice_exist;
                    RAISE NOTICE 'payment_state %', v_payment_state;
                    IF v_invoice_exist IS NULL THEN
                        -- insert invoice
                        INSERT INTO account_move (
                            name, project_id, branch_id,
                            payment_reference, year, currency_id, 
                            date, invoice_date, invoice_date_due, 
                            partner_id, 
                            invoice_payment_term_id, no_faktur_pajak, no_invoice_vendor,
                            state, move_type, journal_id,
                            auto_post, extract_state, company_id, 
                            payment_state,
                            create_date, create_uid
                        ) VALUES (
                            v_doc_number || v_year, v_project_id, v_branch_id,
                            v_doc_number, v_year, v_currency_id,
                            v_posting_date, v_posting_date, v_posting_date, 
                            v_vendor_id, 
                            v_payment_term_id, v_header_text, v_reference,
                            'approved', 'in_invoice', 2,
                            'no', 'no_extract_requested', v_company_id,
                            'Not Request',
                            (now() at time zone 'UTC'), v_uid
                        ) 
                        returning id INTO v_resource_id;
                        RAISE NOTICE 'v_resource_id %', v_resource_id;
                    ELSE
                        IF v_payment_state = 'Not Request' THEN
                            -- update invoice
                            v_resource_id = v_invoice_exist;
                            UPDATE account_move SET
                                name = v_doc_number || v_year, 
                                project_id = v_project_id, 
                                branch_id = v_branch_id,
                                payment_reference = v_doc_number, 
                                year = v_year, 
                                currency_id = v_currency_id, 
                                date = v_posting_date, 
                                invoice_date = v_posting_date, 
                                invoice_date_due = v_posting_date, 
                                partner_id = v_vendor_id, 
                                invoice_payment_term_id = v_payment_term_id, 
                                no_faktur_pajak = v_header_text, 
                                no_invoice_vendor = v_reference,
                                write_date = (now() at time zone 'UTC'), 
                                write_uid = v_uid
                            WHERE id = v_resource_id;
                        END IF;
                    END IF;
                    
                    -- Upsert invoice detail
                    SELECT id FROM account_move_line WHERE move_id = v_resource_id and sequence = v_line_item INTO v_move_line_id;
                    IF v_move_line_id IS NULL THEN
                        -- Insert invoice detail
                        INSERT INTO account_move_line (
                            move_id, move_name, sequence,
                            name, quantity, price_unit, 
                            price_subtotal, amount_sap, pph_cash_basis, 
                            date,
                            parent_state, currency_id, company_currency_id,
                            display_type, account_id, account_root_id,
                            company_id,
                            create_date, create_uid
                        ) VALUES (
                            v_resource_id, v_doc_number || v_year, v_line_item,
                            v_item_text, 1, ABS(v_amount::numeric),
                            ABS(v_amount::numeric), ABS(v_amount::numeric), ABS(v_pph_cbasis::numeric), 
                                                                v_posting_date, 
                            'approved', v_currency_id, 13,
                                                                'product', 67, 53049,
                                                                v_company_id,
                            (now() at time zone 'UTC'), v_uid
                        );
                    ELSE
                        IF v_payment_state = 'Not Request' THEN
                            -- Update invoice detail
                            UPDATE account_move_line SET 
                                move_name = v_doc_number || v_year, 
                                sequence = v_line_item,        
                                name = v_item_text, 
                                quantity = 1, 
                                price_unit = v_amount::numeric, 
                                price_subtotal = v_amount::numeric,
                                amount_sap = v_amount::numeric,
                                pph_cash_basis = ABS(v_pph_cbasis::numeric), 
                                date = v_posting_date,
                                parent_state = 'draft',
                                create_date = (now() at time zone 'UTC'), 
                                create_uid = v_uid
                            WHERE id = v_move_line_id;
                        END IF;
                    END IF;
                            
                    -- update invoice
                    UPDATE account_move SET
                            amount_total_footer = (SELECT SUM(price_subtotal)-SUM(pph_cash_basis) FROM account_move_line WHERE move_id =v_resource_id), 
                            amount_total_payment = (SELECT SUM(price_subtotal)-SUM(pph_cash_basis) FROM account_move_line WHERE move_id =v_resource_id),
                            amount_invoice = (SELECT SUM(price_subtotal) FROM account_move_line WHERE move_id =v_resource_id),
                            amount_untaxed_signed = (SELECT SUM(price_subtotal) FROM account_move_line WHERE move_id =v_resource_id),
                            amount_total_signed = (SELECT SUM(price_subtotal)-SUM(pph_cash_basis) FROM account_move_line WHERE move_id =v_resource_id),
                            amount_total_in_currency_signed = (SELECT SUM(price_subtotal)-SUM(pph_cash_basis) FROM account_move_line WHERE move_id =v_resource_id)
                    WHERE id = v_resource_id;
                        

                    RAISE NOTICE 'SUCCESS %', v_resource_id;
                    
                END LOOP;
                
            END;
            $BODY$
            LANGUAGE plpgsql VOLATILE
            COST 100
            """)

    def get_create_update_invoice_non_po(self):
        ''' This method is called from a cron job.
        '''
        url_config = self.env['wika.integration'].search([('name', '=', 'URL_INV_NON_PO')], limit=1).url
        headers = {
            'Authorization': 'Basic V0lLQV9JTlQ6SW5pdGlhbDEyMw==',
            'Content-Type': 'application/json'
        }

        _logger.info("# === CEK DOC AP NON PO === #")
        docs = self.env['doc.ap.non.po'].search([])
        _logger.info("# === get_create_update_invoice_non_po === #")
        _logger.info(docs)

        for doc in docs:
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

                data_final = []
                if result['DATA']:
                    _logger.info("# === IMPORT DATA === #")
                    company_id = self.env.company.id
                    # diurutkan berdasarakan tahun dan doc number
                    txt_data = sorted(result['DATA'], key=lambda x: (x["YEAR"], x["DOC_NUMBER"]))
                    i = 0
                    sap_codes = []
                    vendors = []
                    for data in txt_data:
                        # _logger.info(data)
                        doc_number = data["DOC_NUMBER"]
                        line_item = data["LINE_ITEM"]
                        year = data["YEAR"]
                        currency = data["CURRENCY"]
                        doc_type = data["DOC_TYPE"]
                        doc_date = data["DOC_DATE"]
                        posting_date = data["POSTING_DATE"]
                        pph_cbasis = data["PPH_CBASIS"]
                        amount = data["AMOUNT"]
                        header_text = data["HEADER_TEXT"]
                        reference = data["REFERENCE"]
                        vendor = data["VENDOR"]
                        top = data["TOP"]
                        item_text = data["ITEM_TEXT"]
                        profit_center = data["PROFIT_CENTER"]

                        # tanggal = datetime.strptime(data['posting_date'], "%Y-%m-%d")
                        # posting_year = tanggal.year
                        project = self.env['project.project'].search([('sap_code', '=', profit_center)], limit=1)
                        _logger.info("# === PROJECT === #")
                        _logger.info(project)
                        partner = self.env['res.partner'].search([('sap_code', '=', vendor)], limit=1)
                        _logger.info("# === PARTNER === #")
                        _logger.info(partner)
                        if project and partner:
                            if project.branch_id != "":
                                recs = [
                                    str(doc_number),
                                    str(line_item), 
                                    str(year),
                                    str(currency),
                                    str(doc_type),
                                    str(doc_date),
                                    str(posting_date),
                                    str(pph_cbasis),
                                    str(amount),
                                    str(header_text),
                                    str(reference),
                                    str(vendor),
                                    str(top),
                                    str(item_text),
                                    str(profit_center),
                                    str(company_id),
                                    str(project.id),
                                    str(project.branch_id.id),
                                    str(partner.id)
                                ]

                                recs = "~~".join(recs)
                                data_final.append(recs)
                                # if profit_center:
                                #     sap_codes.append(str(profit_center))

                        vendors.append(str(vendor))
                        i = i+1

                    data_final = "|".join(data_final)
                    # _logger.info("-----Project %s = %s" % (i, sap_codes))
                    # _logger.info("-----Vendor %s = %s" % (i, vendors))
                    _logger.info("# === DATA FINAL %s = %s" % (i, data_final))

                    cr = self.env.cr
                    cr.execute("select wika_cu_inv_non_po(%s)", (data_final,))
                    _logger.info(_("# === Import Data Berhasil === #"))
                else:
                    raise UserError(_("Data Tidak Tersedia!"))
            except:
                continue
            
        
        
        # self.env.ref('wika_integration.get_create_update_invoice_non_po')._trigger()
    
    def update_doc_bap(self):
        baps = self.env['wika.berita.acara.pembayaran'].search([('state', '=', 'approved')])
        _logger.info("----- BAP -----")
        _logger.info(baps)
        folder_id = self.env['documents.folder'].sudo().search([('name', '=', 'BAP')], limit=1)
        documents_model = self.env['documents.document'].sudo()
        if folder_id:
            facet_id = self.env['documents.facet'].sudo().search([
                ('name', '=', 'Documents'),
                ('folder_id', '=', folder_id.id)
            ], limit=1)
            for bap in baps:    
                _logger.info(bap)
                for doc in bap.document_ids.filtered(lambda x: x.state in ('uploaded','rejected','verified')):
                    # doc.state = 'verified'
                    attachment_id = self.env['ir.attachment'].sudo().create({
                        'name': doc.filename,
                        'datas': doc.document,
                        'res_model': 'documents.document',
                    })
                    if attachment_id:
                        tag = self.env['documents.tag'].sudo().search([
                            ('facet_id', '=', facet_id.id),
                            ('name', '=', doc.document_id.name)
                        ], limit=1)

                        doc_exist = documents_model.search([
                            ('folder_id', '=', folder_id.id),
                            ('partner_id', '=', doc.bap_id.partner_id.id),
                            ('purchase_id', '=', bap.po_id.id),
                            ('bap_id', '=', bap.id)
                        ], limit=1)
                        if not doc_exist:
                            documents_model.create({
                                'attachment_id': attachment_id.id,
                                'folder_id': folder_id.id,
                                'tag_ids': tag.ids,
                                'partner_id': doc.bap_id.partner_id.id,
                                'purchase_id': bap.po_id.id,
                                'bap_id': bap.id,
                            })
            _logger.info("----- BAP BERHASIL -----")