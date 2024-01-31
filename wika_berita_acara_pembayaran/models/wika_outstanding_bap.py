from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
from odoo import tools

class WikaOutstandingBap(models.Model):
    _name = 'wika.outstanding.bap'
    _description = 'Wika Outstanding BAP'
    _auto = False

    purchase_id = fields.Many2one('purchase.order', string='Nomor PO')
    project_id = fields.Many2one('project.project', string='Project')
    branch_id = fields.Many2one('res.branch', string='Divisi')
    po_line = fields.Integer('PO Line')
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Integer(string='Quantity')
    currency_id = fields.Many2one('res.currency', string='Currency')
    unit_price = fields.Monetary(string='Unit Price')
    sub_total = fields.Monetary(string='Subtotal')
    picking_id = fields.Many2one('stock.move', string='NO GR/SES')
    no_gr = fields.Char(string='Nomor GR')
    qty_process = fields.Integer(string='Quantity Proses')
    no_bap = fields.Char(string='Nomor BAP')
    
    
    # @api.model_cr
    # def init(self):
    #     tools.drop_view_if_exists(self._cr, 'wika_berita_acara_pembayaran')
    #     self._cr.execute("""CREATE or REPLACE VIEW wika_outstanding_bap as (
    #         select id as purchase_id from purchase_order)""")
    #     # cr = self.env.cr
    #     # cr.execute("SELECT * FROM purchase_order WHERE active = true")
    #     # result = cr.fetchone()
    #     # print("BERHASILLLLLLLLLLLLLLLL")
    #     print("BERHASILLLLLLLLLLLLLLLL", result)

    # def init(self):
    #     # Ensure the index does not exist before creating it
    #     if not tools.index_exists(self._cr, 'wika_outstanding_bap_custom_index'):
    #         self._cr.execute("""
    #             CREATE INDEX wika_outstanding_bap_custom_index
    #             ON
    #                 wika_outstanding_bap (project_id, branch_id, product_id)
    #         """)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'wika_outstanding_bap_custom_index')
        self.env.cr.execute("""
        CREATE OR replace VIEW vendor_delay_report AS(
        SELECT m.id                     AS id,
            m.date                   AS date,
            m.purchase_line_id       AS purchase_line_id,
            m.product_id             AS product_id,
            Min(pc.id)               AS category_id,
            Min(po.partner_id)       AS partner_id,
            Min(m.product_qty)       AS qty_total,
            Sum(CASE
                    WHEN (m.state = 'done' and pol.date_planned::date >= m.date::date) THEN (ml.qty_done / ml_uom.factor * pt_uom.factor)
                    ELSE 0
                END)                 AS qty_on_time
        FROM   stock_move m
            JOIN purchase_order_line pol
                ON pol.id = m.purchase_line_id
            JOIN purchase_order po
                ON po.id = pol.order_id
            JOIN product_product p
                ON p.id = m.product_id
            JOIN product_template pt
                ON pt.id = p.product_tmpl_id
            JOIN uom_uom pt_uom
                ON pt_uom.id = pt.uom_id
            JOIN product_category pc
                ON pc.id = pt.categ_id
            LEFT JOIN stock_move_line ml
                ON ml.move_id = m.id
            LEFT JOIN uom_uom ml_uom
                ON ml_uom.id = ml.product_uom_id
        GROUP  BY m.id
        )""")