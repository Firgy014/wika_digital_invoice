from odoo import models, fields, api, tools
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
# from odoo import tools


class WikaOutstandingBap(models.Model):
    _name = 'wika.outstanding.bap'
    _description = 'Wika Outstanding BAP'
    _auto = False

    # outstanding
    purchase_id = fields.Many2one('purchase.order', string='Nomor PO')
    product_po_id = fields.Many2one('product.product', string='Purchase Items', default=1)
    sub_total_po = fields.Float(string='Subtotal')
    picking_id = fields.Many2one('stock.picking', string='NO GR/SES')
    product_gr_id = fields.Many2one('product.product', string='Move Items', default=1)
    sub_total_gr = fields.Float(string='Subtotal GR')
    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='BAP Id')
    product_bap_id = fields.Many2one('product.product', string='BAP Id', default=1)
    sub_total_bap = fields.Float(string='Subtotal')
    bap_date = fields.Date(string='Tanggal BAP', required=True, related='bap_id.bap_date')

    # non outstanding
    project_id = fields.Many2one('project.project', string='Project')
    branch_id = fields.Many2one('res.branch', string='Divisi')
    po_line = fields.Integer('PO Line')
    qty = fields.Integer(string='Quantity')
    currency_id = fields.Many2one('res.currency', string='Currency')
    unit_price = fields.Monetary(string='Unit Price')
    no_gr = fields.Char(string='Nomor GR')
    qty_process = fields.Integer(string='Quantity Proses')
    no_bap = fields.Char(string='Nomor BAP')

    # def init(self):
    #     purchase_model = self.env['purchase.order'].sudo()
    #     outstanding_model = self.env['wika.outstanding.bap'].sudo()

    #     total_purchase = purchase_model.search([('id', '!=', False)])
    #     for po in total_purchase:
    #         bap_ids = [(5, 0, 0)]
    #         picking_id = self.env['stock.picking'].search([('po_id', '=', po.id)])
    #         for gr in picking_id:

    #             for move in gr:
    #                 outstanding_id = outstanding_model.create({
    #                     'picking_id': move.id,
    #                     'product_gr_id': move.move_ids_without_package[0].product_id.id,
    #                     # 'sub_total_po': move.product_id.list_price
    #                 })
    #                 outstanding_id.env.cr.commit()

    #         print("TEESSSSSSSSSTTTTTTTT")
    #         print(outstanding_id)
    #         print("TEESSSSSSSSSTTTTTTTT")
    #         # test

            # bap_lines.append((0, 0, {
            #     'picking_id': move.picking_id.id,
            #     'purchase_line_id':move.purchase_line_id.id,
            #     'product_id': move.product_id.id,
            #     'qty': move.product_uom_qty,
            #     'unit_price': move.purchase_line_id.price_unit,
            #     'tax_ids':move.purchase_line_id.taxes_id.ids,
            #     'currency_id':move.purchase_line_id.currency_id.id
            # }))
        
                
    
    
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

    # @api.model_cr
    # def init(self):
    #     tools.drop_view_if_exists(self._cr, 'wika_outstanding_bap')
    #     self._cr.execute("""
    #         CREATE OR REPLACE VIEW wika_outstanding_bap AS (
    #             SELECT  
    #                 po.id AS purchase_id
    #             FROM 
    #                 purchase_order po
    #             WHERE 
    #                 po.state = 'po'
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