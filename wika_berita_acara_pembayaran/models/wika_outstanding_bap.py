from odoo import models, fields, api, tools
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
# from odoo import tools


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
    
    
    # def init(self):
    #     tools.drop_view_if_exists(self._cr, 'wika_berita_acara_pembayaran')
    #     self._cr.execute("""CREATE or REPLACE VIEW wika_outstanding_bap as (
    #         select id as purchase_id from purchase_order)""")
    #     cr = self.env.cr
    #     cr.execute("SELECT * FROM purchase_order WHERE active = true")
    #     result = cr.fetchone()
    #     print("BERHASILLLLLLLLLLLLLLLL")
    #     print("BERHASILLLLLLLLLLLLLLLL", result)

    # def init(self):
    #     # Ensure the index does not exist before creating it
    #     if not tools.index_exists(self._cr, 'wika_outstanding_bap_custom_index'):
    #         self._cr.execute("""
    #             CREATE INDEX wika_outstanding_bap_custom_index
    #             ON
    #                 wika_outstanding_bap (project_id, branch_id, product_id)
    #         """)

    # # @api.model_cr
    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, 'wika_outstanding_bap')
    #     self.env.cr.execute("""
    #         CREATE OR REPLACE VIEW wika_outstanding_bap AS (
    #             SELECT  
    #                 id,
    #                 project_id
    #             FROM 
    #                 purchase_order
    #         )""")

    # def init(self):
    #         tools.drop_view_if_exists(self.env.cr, 'purchase_bill_union')
    #         self.env.cr.execute("""
    #             CREATE OR REPLACE VIEW purchase_bill_union AS (
    #                 SELECT
    #                     id, name, ref as reference, partner_id, date, amount_untaxed as amount, currency_id, company_id,
    #                     id as vendor_bill_id, NULL as purchase_order_id
    #                 FROM account_move
    #                 WHERE
    #                     move_type='in_invoice' and state = 'posted'
    #             UNION
    #                 SELECT
    #                     -id, name, partner_ref as reference, partner_id, date_order::date as date, amount_untaxed as amount, currency_id, company_id,
    #                     NULL as vendor_bill_id, id as purchase_order_id
    #                 FROM purchase_order
    #                 WHERE
    #                     state in ('purchase', 'done') AND
    #                     invoice_status in ('to invoice', 'no')
    #             )""")

    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, self._table)

    #     self.env.cr.execute("""
    #     CREATE OR REPLACE VIEW %s AS (
    #         SELECT  
    #                 id as purhcase_id,
    #                 project_id as project_id
    #             FROM 
    #                 purchase_order
    #     )
    #     """ % (self._table, ))