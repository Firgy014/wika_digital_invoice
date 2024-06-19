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
    wika_state = fields.Selection(selection_add=[
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
        for rec in self:
            _logger.info("# === _recompute_state === #" + str(rec.state))
            res = super(StockMoveInherit, rec)._recompute_state()

        return res

    def _action_assign(self, force_qty=False):
        for rec in self:
            _logger.info("# === _action_assign === #" + str(rec.state))
            res = super(StockMoveInherit, rec)._action_assign()

        return res

    def _get_relevant_state_among_moves(self):
        for rec in self:
            _logger.info("# === _get_relevant_state_among_moves. === #" + str(rec.state))
            res = super(StockMoveInherit, rec)._get_relevant_state_among_moves()

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
            vals['wika_state'] = 'waits'

        # _logger.info('vals_listTTTTTTTTTTTT')
        # _logger.info(vals_list)
        
        res = super(StockMoveLineInherit, self).create(vals_list)
        return res

