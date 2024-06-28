# -*- coding: utf-8 -*-
{
    'name': "Inherit Inventory",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'purchase', 'wika_matrix_approval', 'wika_purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/documents_folder_data.xml',
        'views/filter.xml',
        'views/stock_warehouse_views.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_move_views.xml',
        'views/action.xml',
        'views/menu.xml',
        'views/templates.xml',
        'wizard/wika_reject_reason.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
