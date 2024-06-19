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

    pph_cash_basis = fields.Float(
        string='PPh Cash Basis',
        readonly=False,
        digits='Product Price',
    )

    @api.constrains('account_id', 'display_type')
    def _check_payable_receivable(self):
        return
        # override
        # for line in self:
        # account_type = line.account_id.account_type
        # if line.move_id.is_sale_document(include_receipts=True):
        #     if (line.display_type == 'payment_term') ^ (account_type == 'asset_receivable'):
        #         raise UserError(_("Any journal item on a receivable account must have a due date and vice versa."))
        # if line.move_id.is_purchase_document(include_receipts=True):
        #     if (line.display_type == 'payment_term') ^ (account_type == 'liability_payable'):
        #         raise UserError(_("Any journal item on a payable account must have a due date and vice versa."))
        
    @api.depends('display_type', 'bap_line_id.qty')
    def _compute_quantity(self):
        for line in self:
            if line.display_type == 'product' and line.bap_line_id:
                line.quantity = line.bap_line_id.qty

    @api.onchange('display_type', 'bap_line_id')
    def _onchange_display_type_bap_line_id(self):
        if self.display_type == 'product' and self.bap_line_id:
            self.quantity = self.bap_line_id.qty
        else:
            self.quantity = 0.0 if self.display_type == 'product' else None

    @api.depends('product_id', 'product_uom_id','bap_line_id')
    def _compute_price_unit(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue
            if line.bap_line_id:
                line.price_unit=line.bap_line_id.unit_price
