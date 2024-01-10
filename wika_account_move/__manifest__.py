# -*- coding: utf-8 -*-
{
    'name': "wika_account_move",

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
    'depends': ['base', 'branch', 'project', 'account', 'wika_payment_request', 'wika_berita_acara_pembayaran', 'wika_matrix_approval'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/wika_account_move.xml',
        'data/documents_folder_data.xml',
        'views/action.xml',
        'views/wika_menu.xml',
        'views/templates.xml',
        'wizard/wika_reject_reason.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
