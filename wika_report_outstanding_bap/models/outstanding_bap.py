from odoo import models, fields, api, tools
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
from odoo import tools

class WikaOutstandingBap(models.Model):
    _name = 'outstanding.bap'
    _auto = False

    # outstanding
    branch_id = fields.Many2one('res.branch', string='Divisi')
    purchase_id = fields.Many2one('purchase.order', string='Nomor PO')
    product_po_id = fields.Many2one('product.product', string='Purchase Items')
    #qty_po = fields.Float('QTY PO')
    #sequence_po = fields.Integer (string='Sequence PO')
    #sub_total_po = fields.Float(string='Subtotal PO')
    #picking_id = fields.Many2one('stock.picking', string='NO GR/SES')
    #sequence_gr = fields.Integer (string='Sequence GR')
    #product_gr_id = fields.Many2one('product.product', string='GR Items')
    #qty_gr = fields.Float('QTY GR/SES')
    #sub_total_gr = fields.Float(string='Subtotal GR')
    date_bap = fields.Date(string='Tanggal BAP', required=True)
    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='Nomor BAP')
    #unit_price_bap = fields.Float(string='Unit Price BAP')
    qty_bap = fields.Integer(string='Quantity BAP')
    #product_bap_id = fields.Many2one('product.product', string=' Product BAP')
    sub_total_bap = fields.Float(string='subtotal bap')
    #unit_price_bap = fields.Float(string='Unit Price BAP')
    #price_subtotal_invoice = fields.Float(string='Nilai Invoice')
    potongan_uang_muka_dp = fields.Float(string='Total DP')
    potongan_retensi = fields.Float(string='Total Retensi')
    potongan_uang_muka_qty_dp = fields.Float(string='QTY DP')
    potongan_retensi_qty = fields.Float(string='QTY Retensi')
    # bap_type = fields.Selection(string='Jenis BAP')
    bap_type = fields.Selection([
        ('progress', 'Progress'),
        ('uang muka', 'Uang Muka'),
        ('retensi', 'Retensi'),
        ('cut over', 'Cut Over'),
        ], string='Jenis BAP', default='progress')
    # potongan_retensi = fields.Float(string='Total Retensi')
    # # non outstanding
    # project_id = fields.Many2one('project.project', string='Project')
    # branch_id = fields.Many2one('res.branch', string='Divisi')
    # po_line = fields.Integer('PO Line')
    # qty = fields.Integer(string='Quantity')
    # currency_id = fields.Many2one('res.currency', string='Currency')
    # unit_price = fields.Monetary(string='Unit Price')
    # no_gr = fields.Char(string='Nomor GR')
    # qty_process = fields.Integer(string='Quantity Proses')
    # no_bap = fields.Char(string='Nomor BAP')

    def _get_combined_query(self):
        return"""
        select 
            bal.id as ID, 
            bap.branch_id AS branch_id, 
            bap.po_id AS purchase_id, 
            bal.product_id AS product_po_id, 
            bap.bap_date AS date_bap, 
            bap.id AS bap_id, 
            bal.qty AS qty_bap, 
            CASE WHEN bal.adjustment='t'  
						THEN bal.amount_adjustment
						ELSE (bal.unit_price * bal.qty) END AS sub_total_bap, 
            bap.dp_total AS potongan_uang_muka_dp, 
            bap.retensi_total AS potongan_retensi, 
            bap.dp_qty_total AS potongan_uang_muka_qty_dp, 
            bap.retensi_qty_total AS potongan_retensi_qty, 
            bap.bap_type AS bap_type 
        FROM 
            wika_berita_acara_pembayaran_line bal 
            LEFT JOIN wika_berita_acara_pembayaran bap ON bal.bap_id = bap.id 
        where 
            bal.bap_id is not null  """

        # return """
        # SELECT
        #     bal.id AS id,
        #     po.branch_id AS branch_id,
        #     bap.po_id AS purchase_id,
        #     pol.sequence AS sequence_po,
        #     bal.product_id AS product_po_id,
        #     pol.product_qty AS qty_po,
        #     pol.price_subtotal AS sub_total_po,
        #     bal.picking_id AS picking_id,
        #     pol.sequence AS sequence_gr,
        #     bal.product_id AS product_gr_id,
        #     sm. quantity_done AS qty_gr,
        #     sm.price_unit AS sub_total_gr,
        #     bap.bap_date AS date_bap,
        #     bap.id AS bap_id,
        #     bal.product_id AS product_bap_id,
        #     bal.unit_price AS unit_price_bap,
        #     bal.qty AS qty_bap,
        #     (bal.unit_price * bal.qty) AS sub_total_bap,
        #     aml.price_subtotal AS price_subtotal_invoice,
        #     bap.dp_total AS potongan_uang_muka_dp,
        #     bap.retensi_total AS potongan_retensi,
        #     bap.dp_qty_total AS potongan_uang_muka_qty_dp,
        #     bap.retensi_qty_total AS potongan_retensi_qty
        # FROM
        #     wika_berita_acara_pembayaran_line bal
        # LEFT JOIN
        #     wika_berita_acara_pembayaran bap ON bal.bap_id = bap.id
        # LEFT JOIN
        #     purchase_order po ON bap.po_id = po.id
        # LEFT JOIN
        #     purchase_order_line pol ON bal.product_id = pol.product_id
        # LEFT JOIN
        #     stock_picking sp ON bap.po_id = sp.purchase_id
        # LEFT JOIN
        #     stock_move sm ON sp.id = sm.picking_id
        # LEFT JOIN
        #     account_move_line aml ON bal.id = aml.bap_line_id
        #
        # """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        CREATE OR REPLACE VIEW %s AS (%s)
        """ % (self._table, self._get_combined_query()))

    # def _get_combined_query(self):
    #     return """
    #     SELECT
    #         po.id AS id,
    #         po.id AS purchase_id,
    #         pol.product_id AS product_po_id,
    #         pol.price_subtotal AS sub_total_po,
    #         NULL AS picking_id,
    #         NULL AS product_gr_id
    #     FROM
    #         purchase_order po
    #     LEFT JOIN
    #         purchase_order_line pol ON po.id = pol.order_id
    #     WHERE
    #         po.active = 't'

    #     UNION ALL

    #     SELECT
    #         sp.id AS id,
    #         NULL AS purchase_id,
    #         NULL AS product_po_id,
    #         NULL AS sub_total,
    #         sp.id AS picking_id,
    #         sm.product_id AS product_gr_id
    #     FROM
    #         stock_picking sp
    #     LEFT JOIN
    #         stock_move_line sm ON sp.id = sm.move_id
    #     WHERE
    #         sp.active = 't'
    #     """

    # def _get_combined_query(self):
    # return """
    # SELECT
    #     po.id AS id,
    #     po.id AS purchase_id,
    #     pol.product_id AS product_po_id,
    #     pol.price_subtotal AS sub_total,
    #     NULL AS picking_id,
    #     NULL AS product_gr_id,
    #     NULL AS bap_id
    # FROM
    #     purchase_order po
    # LEFT JOIN
    #     purchase_order_line pol ON po.id = pol.order_id
    # WHERE
    #     po.active = 't'

    # UNION

    # SELECT
    #     sp.id AS id,
    #     NULL AS purchase_id,
    #     NULL AS product_po_id,
    #     NULL AS sub_total,
    #     sp.id AS picking_id,
    #     sm.product_id AS product_gr_id,
    #     NULL AS bap_id
    # FROM
    #     stock_picking sp
    # LEFT JOIN
    #     stock_move_line sm ON sp.id = sm.move_id
    # WHERE
    #     sp.active = 't'

    # UNION

    # SELECT
    #     bap.id AS id,
    #     NULL AS purchase_id,
    #     NULL AS product_po_id,
    #     NULL AS sub_total,
    #     NULL AS picking_id,
    #     NULL AS product_gr_id,
    #     bal.product_id AS product_bap_id
    # FROM
    #     wika_berita_acara_pembayaran bap
    # LEFT JOIN
    #     wika_berita_acara_pembayaran_line bal ON bap.id = bal.bap_id
    # """
    