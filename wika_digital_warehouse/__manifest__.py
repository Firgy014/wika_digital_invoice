# -*- coding: utf-8 -*-
{
    'name': "Wika Digital Warehouse",

    'summary': """
        Wika Digital Warehouse""",

    'description': """
        Wika Digital Warehouse
    """,

    'author': "My Company",
    'website': "https://www.wika.co.id",
    'category': 'Inventory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'purchase', 'wika_matrix_approval', 'wika_purchase', 'wika_inventory', 'branch'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/mail_activity_security.xml',
        'views/views.xml',
        'data/documents_folder_data.xml',

        'wizard/stock_inventory_adjustment_name.xml',
        
        'views/stock_warehouse_views.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_quant_views.xml',
        'views/action.xml',
        'views/menu.xml',
    ],
}
