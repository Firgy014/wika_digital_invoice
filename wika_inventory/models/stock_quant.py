from odoo import models, fields

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # color = fields.Char(
    #     string='Color',
    #     help='The color related to this stock quant.'
    # )
    # title = fields.Char(
    #     string='Title',
    #     help='The title related to this stock quant.'
    # )
    # email = fields.Char(
    #     string='Email',
    #     help='The email related to this stock quant.'
    # )
    # parent_id = fields.Integer('Parent Id')
    # is_company = fields.Boolean('Is Company?')
    # function = fields.Char(
    #     string='Function',
    #     help='The function related to this stock quant.'
    # )
    # phone = fields.Char(
    #     string='Phone',
    #     help='The phone related to this stock quant.'
    # )
    # street = fields.Char(
    #     string='Street',
    #     help='The street related to this stock quant.'
    # )
    # street2 = fields.Char(
    #     string='Street2',
    #     help='The street2 related to this stock quant.'
    # )
    # zip = fields.Char(
    #     string='Zip',
    #     help='The zip related to this stock quant.'
    # )
    # city = fields.Char('City')
    # country_id = fields.Many2one(
    #     'res.country', 
    #     string='Country',
    #     help='The country related to this stock quant.'
    # )
    # mobile = fields.Char('Mobile')
    # sale_order_count = fields.Integer('sale_order_count')
    # purchase_order_count = fields.Integer('purchase_order_count')
    # state_id = fields.Integer('State Id')
    # category_id = fields.Many2one('product.category', 'Category')
    # avatar_128 = fields.Char('avatar_128')
    # type = fields.Char('type')
    # activity_state = fields.Char('activity_state')
    # active = fields.Boolean('Active')
    # activity_ids = fields.Integer('activity_ids')
