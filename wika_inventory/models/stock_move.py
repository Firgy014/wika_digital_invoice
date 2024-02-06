from odoo import models, fields, api

class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    price_subtotal = fields.Float(string='Amount', compute='_compute_price_subtotal')

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
        print('masuk.def.compute.stokmuv')
        for record in self:
            print("qtydon", record.quantity_done)
            print("qtydon", record.quantity_done)
            print("prcunit", record.price_unit)
            # vardump
            print('masuk.for.compute.stokmuv')
            record.price_subtotal = record.quantity_done * record.price_unit