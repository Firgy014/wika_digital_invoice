from odoo import models, fields, api

class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    price_subtotal = fields.Float(string='Amount', compute='_compute_price_subtotal')
    state = fields.Selection(selection_add=[
        ('waits', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')

    ], string='Status', default='waits')
    qty_bap = fields.Float('Total BAP', compute='_compute_qty_bap',digits='Product Unit of Measure')
    sisa_qty_bap = fields.Float('Sisa Qty BAP', compute='_compute_sisa_qty_bap',digits='Product Unit of Measure')
    active = fields.Boolean(default=True)


    def _compute_qty_bap(self):
        for x in self:
            query = """select sum(qty) from wika_berita_acara_pembayaran_line where bap_id is not null and stock_move_id=%s
            """% (x.id)
            # print (query)
            self.env.cr.execute(query)
            result = self.env.cr.fetchone()
            # bap_line_model = self.env['wika.berita.acara.pembayaran.line'].sudo()
            #
            # total_qty = 0
            # bap_line_ids = bap_line_model.search([('stock_move_id', '=', self.id)]).qty
            # bap_lines = bap_line_model.browse(bap_line_ids)
            #
            # for bap_line in bap_lines:
            #     total_qty += bap_line.qty
            if result:
                x.qty_bap = result[0]
            else:
                x.qty_bap=0.0

    @api.depends('qty_bap','quantity_done')
    def _compute_sisa_qty_bap(self):
        for x in self:
            if x.qty_bap>0:
                x.sisa_qty_bap = x.quantity_done - x.qty_bap
            else:
                x.sisa_qty_bap= x.quantity_done
        # bap_line_model = self.env['wika.berita.acara.pembayaran.line'].sudo()
        # bap_line_ids = bap_line_model.search([('picking_id', '=', self.picking_id.id)])
        # if bap_line_ids:
        #     for bap_line in bap_line_ids:
        #         self.sisa_qty_bap = bap_line.qty - self.qty_bap

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

    def name_get(self):
        res = []
        for move in self:
            tit = "[%s] %s" % (move.sequence, move.product_id.code)
            res.append((move.id, tit))
        return res

class StockMoveLineInherit(models.Model):
    _inherit = 'stock.move.line'

    active = fields.Boolean(default=True)

