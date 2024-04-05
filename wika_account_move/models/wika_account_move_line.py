from odoo import fields, models,api

class WikaAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    branch_id = fields.Many2one('res.branch', string='Divisi',related='move_id.branch_id')
    department_id = fields.Many2one('res.branch', string='Department',related='move_id.department_id')
    project_id = fields.Many2one('project.project', string='Project',related='move_id.project_id')
    bap_line_id = fields.Many2one('wika.berita.acara.pembayaran.line', string='BAP Line Id', widget='many2one')
    purchase_id = fields.Many2one('purchase.order', string='NO PO',related='purchase_line_id.order_id')
    picking_id = fields.Many2one('stock.picking', string='NO GR/SES')
    stock_move_id = fields.Many2one('stock.move', string='Item GR/SES')
    amount_sap = fields.Float(string='Amount SAP')
    cut_off = fields.Boolean(string='Cut Off',related='move_id.cut_off',default=False,copy=False)

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
    adjustment = fields.Boolean(string='Adjustment', default=False)
    amount_adjustment = fields.Monetary(string='Amount Adjustment')
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
