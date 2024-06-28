import logging
_logger = logging.getLogger(__name__)

try:
    import paramiko
except ImportError:
    raise ImportError(
        'This module needs paramiko to automatically write backups to the FTP through SFTP. Please install paramiko on your system. (sudo pip3 install paramiko)')

def _get_computed_query():
    return """
SELECT
	inv.name as NO,
    TO_CHAR(inv.invoice_date, 'yyyymmdd') AS DOC_DATE,
    TO_CHAR(inv.date, 'yyyymmdd') AS PSTNG_DATE,
    inv.no_invoice_vendor AS REF_DOC_NO,
    ROUND(inv.amount_invoice) AS GROSS_AMOUNT,
    TO_CHAR(inv.baseline_date, 'yyyymmdd') AS BLINE_DATE,
    inv.no_faktur_pajak AS HEADER_TXT,
    line.name AS ITEM_TEXT,
    acc.code AS HKONT,
    CASE
    WHEN inv.retensi_total > 0 THEN CAST(inv.amount_invoice - inv.retensi_total AS VARCHAR)
    ELSE '' 
END AS TAX_BASE_AMOUNT,
    tax_group.pph_group_code AS WI_TAX_TYPE,
    tax.pph_code AS WI_TAX_CODE,
    '' AS WI_TAX_BASE,
    po.name AS PO_NUMBER,
    pol.sequence AS PO_ITEM,
    CASE
        WHEN sp.pick_type = 'ses' THEN ''
        ELSE sp.name
    END AS REF_DOC,
    CASE 
        WHEN po.po_type != 'JASA' THEN to_char(sp.date, 'yyyy')
        ELSE ''
    END AS REF_DOC_YEAR,
    CASE 
        WHEN po.po_type = 'BARANG' THEN CAST(sm.sequence AS VARCHAR)
        ELSE '' END AS REF_DOC_IT,
                                                                                                   
    CASE 
        WHEN line.amount_adjustment>0 THEN line.amount_adjustment
        ElSE line.price_subtotal END AS ITEM_AMOUNT,
    line.quantity as QUANTITY,
    CASE
        WHEN po.po_type = 'JASA' THEN sp.name
        ELSE ''
    END AS SHEET_NO,
    CASE
        WHEN inv.retensi_total>0 THEN to_char(inv.retention_due, 'yyyymmdd')
        ELSE to_char(inv.invoice_date_due, 'yyyymmdd')
    END AS RETENTION_DUE_DATE,
CASE 
    WHEN inv.dp_total > 0 THEN 'X'
    ELSE '' 
END AS IND_DP,
CASE 
    WHEN inv.dp_total > 0 THEN CAST(inv.dp_total AS VARCHAR)
    ELSE '' 
END AS DP_AMOUNT
FROM 
    account_move inv
LEFT JOIN 
    account_move_line line ON line.move_id = inv.id
LEFT JOIN 
    account_move_account_tax_rel pph ON pph.account_move_id = inv.id
LEFT JOIN 
    account_tax tax ON tax.id = pph.account_tax_id
LEFT JOIN
    account_account acc ON acc.id = inv.account_id
LEFT JOIN
    account_tax_group tax_group ON tax_group.id = tax.tax_group_id
LEFT JOIN
    purchase_order po ON po.id = inv.po_id
LEFT JOIN
    wika_berita_acara_pembayaran_line bap_line ON bap_line.id = line.bap_line_id
LEFT JOIN
    product_product prod ON prod.id = line.product_id
left JOIN
    stock_move sm ON sm.id=line.stock_move_id
LEFT JOIN
    stock_picking sp ON sp.id = sm.picking_id
LEFT JOIN
    purchase_order_line pol ON pol.id = sm.purchase_line_id
WHERE 
     inv.is_mp_approved = True AND line.display_type = 'product' and inv.cut_off!=True and inv.invoice_number is null 
     AND (line.amount_adjustment > 0 OR line.price_subtotal != 0);
"""

def _get_computed_query_scf():
    return """
SELECT
    inv.name AS NO,
    inv.payment_reference AS DOC_NUMBER,
    CASE WHEN pricecutline.posting_date IS NULL THEN TO_CHAR(current_date, 'YYYY') ELSE TO_CHAR(pricecutline.posting_date, 'YYYY') END AS DOC_YEAR,
    CASE WHEN pricecutline.posting_date IS NULL THEN TO_CHAR(current_date, 'YYYYMMDD') ELSE TO_CHAR(pricecutline.posting_date, 'YYYYMMDD') END AS POSTING_DATE,
    CASE WHEN pricecutline.posting_date IS NULL THEN TO_CHAR(current_date, 'FMmm') ELSE TO_CHAR(pricecutline.posting_date, 'FMmm') END AS PERIOD,
    pricecutline.amount AS AMOUNT_SCF,
    pricecutline.wbs_project_definition AS WBS,
    product.name->>'en_US' AS ITEM_TEXT
FROM
    account_move inv
LEFT JOIN
    wika_account_move_pricecut_line pricecutline ON pricecutline.move_id = inv.id
LEFT JOIN
    product_template product ON product.name->>'en_US' = 'Potongan SCF'
WHERE
    pricecutline.amount > 0
    AND pricecutline.wbs_project_definition != ''
    AND pricecutline.is_scf != true;
"""

def _get_computed_partial_payment_query():
    return """
      SELECT
        pp.name as NO,
        am.payment_reference as DOC_NUMBER,
          TO_CHAR(am.invoice_date, 'yyyy') AS DOC_YEAR,
          TO_CHAR(pp.posting_date, 'yyyymmdd') AS POSTING_DATE,
          TO_CHAR(pp.posting_date, 'mm')::int AS PERIOD,
          ROUND(pp.partial_amount) AS AMOUNT1,
          ROUND(pp.total_invoice - pp.partial_amount) AS AMOUNT2
      FROM 
          wika_partial_payment_request pp
      LEFT JOIN account_move am ON am.id = pp.invoice_id
      WHERE 
          pp.state = 'approved'
        AND (pp.total_invoice - pp.partial_amount) > 0
        AND pp.no_doc_sap IS NULL 
      """

def _get_computed_query_dp():
    return """
SELECT
    inv.name AS NO,
    TO_CHAR(inv.invoice_date, 'YYYYMMDD') AS DOC_DATE,
    TO_CHAR(inv.date, 'YYYYMMDD') AS POSTING_DATE,
    TO_CHAR(inv.date, 'FMmm') AS PERIOD,
    currency.name AS CURRENCY,
    inv.no_invoice_vendor AS REFERENCE,
    inv.no_faktur_pajak AS HEADER_TXT,
    partner.sap_code AS ACC_VENDOR,
    TO_CHAR(inv.special_gl_id, '') AS SPECIAL_GL,
    inv.amount_invoice AS AMOUNT,
    tax.name->>'en_US' AS TAX_CODE,
    TO_CHAR(inv.invoice_date_due, 'YYYYMMDD') AS DUE_ON,
    po.name AS PO_NUMBER,
    COALESCE(pol.sequence, 10) AS PO_ITEM,
    proj.sap_code AS PROFIT_CTR,
    line.name AS TEXT,
    wht_tax_group.name->>'en_US' AS WHT_TYPE,
    wht_tax.pph_code AS WHT_CODE
FROM
    account_move inv
LEFT JOIN
    res_currency currency ON currency.id = inv.currency_id
LEFT JOIN
    res_partner partner ON partner.id = inv.partner_id
LEFT JOIN
    account_move_line line ON line.move_id = inv.id
LEFT JOIN
    account_move_account_tax_rel pph ON pph.account_move_id = inv.id
LEFT JOIN
    account_move_line_account_tax_rel tax_line_rel ON tax_line_rel.account_move_line_id = line.id
LEFT JOIN
    account_tax tax ON tax.id = tax_line_rel.account_tax_id
LEFT JOIN
    account_tax_group tax_group ON tax_group.id = tax.tax_group_id
LEFT JOIN
    purchase_order po ON po.id = inv.po_id
LEFT JOIN
    project_project proj ON proj.id = inv.project_id
LEFT JOIN
    purchase_order_line pol ON pol.id = line.purchase_line_id
LEFT JOIN
    account_tax wht_tax ON wht_tax.id = pph.account_tax_id
LEFT JOIN
    account_tax_group wht_tax_group ON wht_tax_group.id = wht_tax.tax_group_id
WHERE
    inv.is_mp_approved = true AND
    inv.bap_type = 'uang muka' AND
    line.display_type = 'product' AND
    inv.payment_reference IS NULL;
"""

def _get_computed_query_retensi():
    return """
SELECT
    inv.name AS NO,
    TO_CHAR(inv.date, 'YYYYMMDD') AS POSTING_DATE,
    TO_CHAR(inv.date, 'FMmm') AS PERIOD,
    TO_CHAR(inv.date, 'FMyyyy') AS YEAR,
    currency.name AS CURRENCY,
    inv.no_invoice_vendor AS REFERENCE,
    inv.no_faktur_pajak AS HEADER_TEXT,
    partner.sap_code AS VENDOR,
    inv.amount_invoice AS AMOUNT,
    po.name AS ASSIGNMENT,
    CONCAT(partner.sap_code, '-', partner.name) AS ITEM_TEXT,
    CASE WHEN inv.project_id IS NOT NULL THEN proj.sap_code ELSE branch.sap_code END AS PROFIT_CENTER,
    (SELECT tax.pph_code
    FROM account_move_line line
    JOIN account_move_line_account_tax_rel rel ON rel.account_move_line_id = line.id
    JOIN account_tax tax ON tax.id = rel.account_tax_id
    WHERE line.move_id = inv.id
    LIMIT 1) AS TAX_CODE
FROM
    account_move inv 
LEFT JOIN
    res_branch branch ON branch.id = inv.branch_id 
LEFT JOIN
    res_partner partner ON partner.id = inv.partner_id 
LEFT JOIN
    account_move_line line ON line.move_id = inv.id 
LEFT JOIN
    res_currency currency ON currency.id = inv.currency_id
LEFT JOIN
    purchase_order po ON po.id = inv.po_id 
LEFT JOIN
    project_project proj ON proj.id = inv.project_id 
WHERE
    inv.is_mp_approved = true
    AND inv.bap_type = 'retensi'  
    AND line.display_type = 'product'
    AND inv.payment_reference IS NULL;
"""

def _get_computed_query_reclass_ppn_waba(payment_id):
    return f"""
SELECT
    inv.name AS NO,
    inv.payment_reference AS DOC_NUMBER,
    TO_CHAR(inv.date, 'YYYY') AS DOC_YEAR,
    TO_CHAR(inv.date, 'YYYYMMDD') AS POSTING_DATE,
    TO_CHAR(inv.date, 'FMmm') AS PERIOD
FROM
    wika_payment_request pay
LEFT JOIN
    account_move_wika_payment_request_rel rel ON pay.id = {payment_id.id}
LEFT JOIN
    account_move inv ON inv.id = rel.account_move_id
WHERE
    pay.id = {payment_id.id}
    AND pay.is_sent_to_sap = false    
    AND inv.payment_reference IS NOT NULL
    AND inv.is_waba = true

UNION

SELECT
    partial_inv.name AS NO,
    partial_inv.payment_reference AS DOC_NUMBER,
    TO_CHAR(partial_inv.date, 'YYYY') AS DOC_YEAR,
    TO_CHAR(partial_inv.date, 'YYYYMMDD') AS POSTING_DATE,
    TO_CHAR(partial_inv.date, 'FMmm') AS PERIOD
FROM
    wika_payment_request pay
LEFT JOIN
    wika_partial_payment_request_wika_payment_request_rel partial_rel ON pay.id = {payment_id.id}
LEFT JOIN
    wika_partial_payment_request partial_pay ON partial_pay.id = partial_rel.wika_partial_payment_request_id
LEFT JOIN
    account_move partial_inv ON partial_inv.id = partial_pay.invoice_id
WHERE
    pay.id = {payment_id.id}
    AND partial_inv.payment_reference IS NOT NULL
    AND partial_inv.is_waba = true;
"""
