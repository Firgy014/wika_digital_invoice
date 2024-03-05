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
    (CASE 
        WHEN (tax_group.name->>'en_US') ~ '\d+\.?\d*%' THEN (tax_group.name->>'en_US')
        ELSE tax_group.name->>'en_US'
    END) AS WI_TAX_TYPE,
    (CASE 
        WHEN (tax.name->>'en_US') ~ '\d+\.?\d*%' THEN (tax.name->>'en_US')
        ELSE tax.name->>'en_US'
    END) AS WI_TAX_CODE,
    inv.total_line AS WI_TAX_BASE,
    po.name AS PO_NUMBER,
    pol.sequence AS PO_ITEM,
    CASE
        WHEN sp.pick_type = 'SES' THEN sp.origin
        ELSE sp.name
    END AS REF_DOC,
    CASE 
        WHEN po.po_type = 'JASA' THEN to_char(po.begin_date, 'yyyy')
        ELSE ''
    END AS REF_DOC_YEAR,
    CASE 
        WHEN po.po_type = 'BARANG' THEN prod.default_code
        ELSE ''
    END AS REF_DOC_IT,                                                                                                                  
    line.price_subtotal AS ITEM_AMOUNT,
    line.quantity as QUANTITY,
    CASE
        WHEN po.po_type = 'JASA' THEN sp.name
        ELSE ''
    END AS SHEET_NO
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
    purchase_order_line pol ON pol.id = line.purchase_line_id
LEFT JOIN
    product_product prod ON prod.id = line.product_id
LEFT JOIN
    wika_berita_acara_pembayaran_line bap_line ON bap_line.id = line.bap_line_id
LEFT JOIN
    stock_picking sp ON sp.id = bap_line.picking_id
WHERE 
    inv.state = 'approved'
"""