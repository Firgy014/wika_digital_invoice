from odoo import models, fields, api, _
from datetime import datetime
from collections import defaultdict
from odoo.exceptions import AccessError, ValidationError
from datetime import datetime, timedelta
import logging, json
_logger = logging.getLogger(__name__)

class PickingInherit(models.Model):
    _inherit = "stock.picking"
    
    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.ensure_one()
        self.partner_id = self.branch_id.partner_id


    @api.onchange('po_id')
    def _onchange_purchase_auto_complete(self):
        _logger.info("# === _onchange_purchase_auto_complete === #")
        
        if not self.po_id:
            return
        
        # Copy data from PO
        picking_vals = self.po_id._prepare_stock_picking()
        self.update(picking_vals)

        po_lines = self.po_id.order_line - self.move_ids.mapped('purchase_line_id')
        for line in po_lines.filtered(lambda l: not l.display_type):
            self.move_ids += self.env['stock.move'].new(
                line._prepare_stock_move(self)
            )
            _logger.info('# === ADD STOCK MOVE BARANG === #')
            # # stock_move.create(vals)
            # self.invoice_line_ids += .write({
            #     'move_ids': [(0, 0, {
            #         'sequence': item['MATDOC_ITM'],
            #         'product_id': prod.id if prod else False,
            #         'quantity_done': qty,
            #         'product_uom_qty': qty,
            #         'product_uom': uom.id,
            #         #'active':active,
            #         'state': 'waits',
            #         'location_id': 4,
            #         'location_dest_id': 8,
            #         'purchase_line_id': po_line.id,
            #         'name': prod.display_name if prod else False,
            #         'origin': rec.name,
            #     })],
            #     'active': active
            # })

        # Compute gr ses origin.
        origins = set(self.move_ids.mapped('purchase_line_id.order_id.name'))
        self.origin = ','.join(list(origins))
