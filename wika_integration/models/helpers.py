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
    ROUND(inv.amount_untaxed) AS GROSS_AMOUNT,
    TO_CHAR(inv.baseline_date, 'yyyymmdd') AS BLINE_DATE,
    inv.no_faktur_pajak AS HEADER_TXT,
    line.name AS ITEM_TEXT,
    acc.code AS HKONT,
    CASE
    WHEN inv.retensi_total > 0 THEN CAST(inv.amount_untaxed - inv.retensi_total AS VARCHAR)
    ELSE '' 
END AS TAX_BASE_AMOUNT,
    tax_group.pph_group_code AS WI_TAX_TYPE,
    tax.pph_code AS WI_TAX_CODE,
    '' AS WI_TAX_BASE,
    po.name AS PO_NUMBER,
    pol.sequence AS PO_ITEM,
    CASE
        WHEN sp.pick_type = 'SES' THEN sp.origin
        ELSE sp.name
    END AS REF_DOC,
    CASE 
        WHEN po.po_type != 'JASA' THEN to_char(po.begin_date, 'yyyy')
        ELSE ''
    END AS REF_DOC_YEAR,
    CASE 
        WHEN po.po_type = 'BARANG' THEN CAST(sm.sequence AS VARCHAR)
        ELSE '' END AS REF_DOC_IT,
                                                                                                   
    line.price_subtotal AS ITEM_AMOUNT,
    line.quantity as QUANTITY,
    CASE
        WHEN po.po_type = 'JASA' THEN sp.name
        ELSE ''
    END AS SHEET_NO,
    CASE
        WHEN inv.retention_due IS NOT NULL THEN to_char(inv.invoice_date_due, 'yyyymmdd')
        ELSE to_char(inv.date, 'yyyymmdd')
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
    purchase_order_line pol ON pol.id = bap_line.purchase_line_id
LEFT JOIN
    product_product prod ON prod.id = line.product_id
LEFT JOIN
    stock_picking sp ON sp.id = bap_line.picking_id
left JOIN
    stock_move sm ON sm.id=line.stock_move_id
WHERE 
     inv.is_mp_approved = True AND line.display_type = 'product' and inv.cut_off!=True and inv.invoice_number is null
"""