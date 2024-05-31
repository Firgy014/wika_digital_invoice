from collections import defaultdict
from datetime import timedelta
from operator import itemgetter

from odoo import _, api, Command, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet, groupby

import logging, json
_logger = logging.getLogger(__name__)

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
    
    def _recompute_state(self):
        _logger.info("# === _recompute_state === #" + str(self.state))
        return
        # moves_state_to_write = defaultdict(set)
        # for move in self:
        #     rounding = move.product_uom.rounding
        #     if move.state in ('waits', 'uploaded', 'approved', 'rejected'):
        #         continue
        #     elif float_compare(move.reserved_availability, move.product_uom_qty, precision_rounding=rounding) >= 0:
        #         moves_state_to_write['assigned'].add(move.id)
        #     elif move.reserved_availability and float_compare(move.reserved_availability, move.product_uom_qty, precision_rounding=rounding) <= 0:
        #         moves_state_to_write['partially_available'].add(move.id)
        #     elif move.procure_method == 'make_to_order' and not move.move_orig_ids:
        #         moves_state_to_write['waiting'].add(move.id)
        #     elif move.move_orig_ids and any(orig.state not in ('done', 'cancel') for orig in move.move_orig_ids):
        #         moves_state_to_write['waiting'].add(move.id)
        #     else:
        #         moves_state_to_write['confirmed'].add(move.id)
        # for state, moves_ids in moves_state_to_write.items():
            # self.browse(moves_ids).filtered(lambda m: m.state != state).state = state

    def _action_assign(self, force_qty=False):
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `reserved_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """
        StockMove = self.env['stock.move']
        assigned_moves_ids = OrderedSet()
        partially_available_moves_ids = OrderedSet()
        # Read the `reserved_availability` field of the moves out of the loop to prevent unwanted
        # cache invalidation when actually reserving the move.
        reserved_availability = {move: move.reserved_availability for move in self}
        roundings = {move: move.product_id.uom_id.rounding for move in self}
        move_line_vals_list = []
        # Once the quantities are assigned, we want to find a better destination location thanks
        # to the putaway rules. This redirection will be applied on moves of `moves_to_redirect`.
        moves_to_redirect = OrderedSet()
        moves_to_assign = self
        if not force_qty:
            moves_to_assign = self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available'])
        for move in moves_to_assign:
            rounding = roundings[move]
            if not force_qty:
                missing_reserved_uom_quantity = move.product_uom_qty
            else:
                missing_reserved_uom_quantity = force_qty
            missing_reserved_uom_quantity -= reserved_availability[move]
            missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity, move.product_id.uom_id, rounding_method='HALF-UP')
            if move._should_bypass_reservation():
                # create the move line(s) but do not impact quants
                if move.move_orig_ids:
                    available_move_lines = move._get_available_move_lines(assigned_moves_ids, partially_available_moves_ids)
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        qty_added = min(missing_reserved_quantity, quantity)
                        move_line_vals = move._prepare_move_line_vals(qty_added)
                        move_line_vals.update({
                            'location_id': location_id.id,
                            'lot_id': lot_id.id,
                            'lot_name': lot_id.name,
                            'owner_id': owner_id.id,
                        })
                        move_line_vals_list.append(move_line_vals)
                        missing_reserved_quantity -= qty_added
                        if float_is_zero(missing_reserved_quantity, precision_rounding=move.product_id.uom_id.rounding):
                            break

                if missing_reserved_quantity and move.product_id.tracking == 'serial' and (move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                    for i in range(0, int(missing_reserved_quantity)):
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=1))
                elif missing_reserved_quantity:
                    to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                            ml.location_id == move.location_id and
                                                            ml.location_dest_id == move.location_dest_id and
                                                            ml.picking_id == move.picking_id and
                                                            not ml.lot_id and
                                                            not ml.package_id and
                                                            not ml.owner_id)
                    if to_update:
                        to_update[0].reserved_uom_qty += move.product_id.uom_id._compute_quantity(
                            missing_reserved_quantity, move.product_uom, rounding_method='HALF-UP')
                    else:
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=missing_reserved_quantity))
                assigned_moves_ids.add(move.id)
                moves_to_redirect.add(move.id)
            else:
                if float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                    assigned_moves_ids.add(move.id)
                elif not move.move_orig_ids:
                    if move.procure_method == 'make_to_order':
                        continue
                    # If we don't need any quantity, consider the move assigned.
                    need = missing_reserved_quantity
                    if float_is_zero(need, precision_rounding=rounding):
                        assigned_moves_ids.add(move.id)
                        continue
                    # Reserve new quants and create move lines accordingly.
                    forced_package_id = move.package_level_id.package_id or None
                    available_quantity = move._get_available_quantity(move.location_id, package_id=forced_package_id)
                    if available_quantity <= 0:
                        continue
                    taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id, package_id=forced_package_id, strict=False)
                    if float_is_zero(taken_quantity, precision_rounding=rounding):
                        continue
                    moves_to_redirect.add(move.id)
                    if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
                        assigned_moves_ids.add(move.id)
                    else:
                        partially_available_moves_ids.add(move.id)
                else:
                    # Check what our parents brought and what our siblings took in order to
                    # determine what we can distribute.
                    # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                    # the reserved quantity on the quants, convert it here in
                    # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                    available_move_lines = move._get_available_move_lines(assigned_moves_ids, partially_available_moves_ids)
                    if not available_move_lines:
                        continue
                    for move_line in move.move_line_ids.filtered(lambda m: m.reserved_qty):
                        if available_move_lines.get((move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)):
                            available_move_lines[(move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)] -= move_line.reserved_qty
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        need = move.product_qty - sum(move.move_line_ids.mapped('reserved_qty'))
                        # `quantity` is what is brought by chained done move lines. We double check
                        # here this quantity is available on the quants themselves. If not, this
                        # could be the result of an inventory adjustment that removed totally of
                        # partially `quantity`. When this happens, we chose to reserve the maximum
                        # still available. This situation could not happen on MTS move, because in
                        # this case `quantity` is directly the quantity on the quants themselves.
                        available_quantity = move._get_available_quantity(location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
                        if float_is_zero(available_quantity, precision_rounding=rounding):
                            continue
                        taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity), location_id, lot_id, package_id, owner_id)
                        if float_is_zero(taken_quantity, precision_rounding=rounding):
                            continue
                        moves_to_redirect.add(move.id)
                        if float_is_zero(need - taken_quantity, precision_rounding=rounding):
                            assigned_moves_ids.add(move.id)
                            break
                        partially_available_moves_ids.add(move.id)
            if move.product_id.tracking == 'serial':
                move.next_serial_count = move.product_uom_qty

        _logger.info("# === _action_assign === #" + str(self.state))
        self.env['stock.move.line'].create(move_line_vals_list)
        # StockMove.browse(partially_available_moves_ids).write({'state': 'partially_available'})
        # StockMove.browse(assigned_moves_ids).write({'state': 'assigned'})
        # if not self.env.context.get('bypass_entire_pack'):
        #     self.mapped('picking_id')._check_entire_pack()
        # StockMove.browse(moves_to_redirect).move_line_ids._apply_putaway_strategy()

    def _get_relevant_state_among_moves(self):
        _logger.info("# === _get_relevant_state_among_moves === #" + str(self.state))
        res = super(StockMoveInherit, self)._get_relevant_state_among_moves()

        return res

    def write(self, vals):
        _logger.info(str(vals.get('state')) + "# === WRITE === #" + str(self.state))
        res = super(StockMoveInherit, self).write(vals)

        return res
    
    def _merge_moves_fields(self):
        _logger.info("# === _merge_moves_fields === #" + str(self.state))
        res = super(StockMoveInherit, self)._merge_moves_fields()

        return res

class StockMoveLineInherit(models.Model):
    _inherit = 'stock.move.line'

    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['state'] = 'waits'

        # _logger.info('vals_listTTTTTTTTTTTT')
        # _logger.info(vals_list)
        
        res = super(StockMoveLineInherit, self).create(vals_list)
        return res

