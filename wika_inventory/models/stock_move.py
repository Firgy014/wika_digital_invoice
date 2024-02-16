from odoo import models, fields, api

class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    price_subtotal = fields.Float(string='Amount', compute='_compute_price_subtotal')
    qty_bap = fields.Integer('Total BAP', compute='_compute_qty_bap')
    sisa_qty_bap = fields.Integer('Total BAP', compute='_compute_sisa_qty_bap')
    
    def _compute_qty_bap(self):
        bap_line_model = self.env['wika.berita.acara.pembayaran.line'].sudo()
        # purchase_line_model = self.env['purchase.order.line'].sudo()

        total_qty = 0
        bap_line_ids = bap_line_model.search([('picking_id', '=', self.picking_id.id)])
        if bap_line_ids:
            for bap_line in bap_line_ids:
                total_qty += bap_line.qty

        self.qty_bap = total_qty

    @api.depends('qty_bap')
    def _compute_sisa_qty_bap(self):
        bap_line_model = self.env['wika.berita.acara.pembayaran.line'].sudo()
        bap_line_ids = bap_line_model.search([('picking_id', '=', self.picking_id.id)])
        if bap_line_ids:
            for bap_line in bap_line_ids:
                self.sisa_qty_bap = bap_line.qty - self.qty_bap

    # @api.model_create_multi
    # def create(self, vals_list):
    #     print("this is vals list", vals_list)
    #     for vals in vals_list:
    #         res = super(StockMoveInherit, self).create(vals)

    #         print("this is vals", vals)

    #     print("this is res before returned", res)
    #     vardump_stockmove_create
    #     return res
    
    @api.depends('quantity_done', 'price_unit')
    def _compute_price_subtotal(self):
        for record in self:
            record.price_subtotal = record.quantity_done * record.price_unit