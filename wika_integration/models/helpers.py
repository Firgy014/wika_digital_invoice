def _get_computed_query():
    return """
SELECT                  
    to_char(inv.invoice_date, 'yyyymmdd') AS DOC_DATE,
    to_char(inv.date, 'yyyymmdd') AS PSTNG_DATE,
    inv.no_invoice_vendor AS REF_DOC_NO,
    inv.total_line AS GROSS_AMOUNT,
    inv.baseline_date AS BLINE_DATE,
    inv.no_faktur_pajak AS HEADER_TXT,
    line.name AS ITEM_TEXT,
    acc.code AS HKONT,
    inv.retention_due AS RETENTION_DUE_DATE,
    inv.total_line AS TAX_BASE_AMOUNT,
    tax_group.name AS WI_TAX_TYPE,
    pph.name AS WI_TAX_CODE,
    inv.total_line AS WI_TAX_BASE,
    po.name AS PO_NUMBER,
    pol.sequence AS PO_ITEM,
    po.begin_date AS REF_DOC_YEAR,                                                                                                                  
    prod.default_code AS REF_DOC_IT,
    sp.name AS SHEET_NO,
    line.price_subtotal AS ITEM_AMOUNT,
    line.quantity as QUANTITY
FROM 
    account_move inv
LEFT JOIN 
    account_move_line line ON line.move_id = inv.id
LEFT JOIN 
    account_tax pph ON pph.move_id = inv.id
LEFT JOIN
    account_account acc ON acc.id = inv.account_id
LEFT JOIN
    account_tax_group tax_group ON tax_group.id = pph.tax_group_id
LEFT JOIN
    purchase_order po ON po.id = inv.po_id
LEFT JOIN
    purchase_order_line pol ON pol.id = line.purchase_line_id
LEFT JOIN
    product_product prod ON prod.id = line.product_id
LEFT JOIN
    wika_berita_acara_pembayaran_line bap_line ON bap_line.id = line.bap_line_id
LEFT JOIN
    stock_picking sp ON sp.id = bap_line.picking_id
"""