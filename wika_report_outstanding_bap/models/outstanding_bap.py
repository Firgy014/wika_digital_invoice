from odoo import models, fields, api, tools
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
from odoo import tools

# class PurchaseOrder(models.Model):
#     _inherit = 'purchase.order'
#     _name = 'purchase.order'

#     asu_ids = fields.One2many('wika.outstanding.bap', 'purchase_id', string='Your Models')

class WikaOutstandingBap(models.Model):
    _name = 'outstanding.bap'
    _auto = False

    # outstanding
    purchase_id = fields.Many2one('purchase.order', string='Nomor PO')
    product_po_id = fields.Many2one('product.product', string='Purchase Items')
    sub_total_po = fields.Float(string='Subtotal')
    picking_id = fields.Many2one('stock.picking', string='NO GR/SES')
    # product_gr_id = fields.Many2one('product.product', string='Move Items')
    # sub_total_gr = fields.Float(string='Subtotal GR')
    # bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='BAP Id')
    # product_bap_id = fields.Many2one('product.product', string=' Product BAP')
    # sub_total_bap = fields.Float(string='Subtotal')
    # bap_date = fields.Date(string='Tanggal BAP', required=True, related='bap_id.bap_date')

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
    def _get_combined_query(self):
        return """
        SELECT
            pol.id AS id,
            po.id AS purchase_id,
            pol.product_id AS product_po_id,
            pol.price_subtotal AS sub_total_po,
            sp.id AS picking_id
        FROM
            purchase_order_line pol
        LEFT JOIN
            purchase_order po ON po.id = pol.order_id
        LEFT JOIN
            stock_picking sp ON po.id = sp.purchase_id
        WHERE
            po.active = 't'
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        CREATE OR REPLACE VIEW %s AS (%s)
        """ % (self._table, self._get_combined_query()))
