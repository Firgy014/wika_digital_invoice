# -*- coding: utf-8 -*-
{
    'name': "wika_noncash_loan",

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
    'depends': ['base', 'branch', 'wika_project', 'mail' ,'wika_plafond_bank', 'wika_cash_loan'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        # 'views/wika_ncl_input.xml',
        'views/wika_ncl_proses.xml',
        'views/wika_ncl_pembayaran.xml',
        'views/wika_plafond_bank_inherit.xml',
        'views/wika_menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
