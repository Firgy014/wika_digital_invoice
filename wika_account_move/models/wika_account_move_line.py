from odoo import fields, models,api

class WikaAccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    bap_line_id = fields.Many2one('wika.berita.acara.pembayaran.line', string='BAP Line Id', widget='many2one')
    # asw_tnat = fields.Char('asw tnat')
    quantity = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        compute='_compute_quantity', store=True, readonly=False, precompute=True,

        help="The optional quantity expressed by this line, eg: number of product sold. "
             "The quantity is not a legal requirement but is very useful for some reports.",
    )
    price_unit = fields.Float(
        string='Unit Price',
        compute="_compute_price_unit", store=True, readonly=False, precompute=True,
        digits='Product Price',
    )
    @api.depends('display_type','bap_line_id')
    def _compute_quantity(self):
        for line in self:
            line.quantity = line.bap_line_id.qty if line.display_type == 'product' and line.bap_line_id else False

    @api.depends('product_id', 'product_uom_id','bap_line_id')
    def _compute_price_unit(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue
            if line.bap_line_id:
                line.price_unit=line.bap_line_id.unit_price
