# -*- coding: utf-8 -*-
{
    'name': "wika_flafond_bank",

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
    'depends': ['base','mail', 'branch'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/wika_loan_jenis.xml',
        'views/wika_menu.xml',
        'views/wika_plafond_bank.xml',
        'views/wika_loan_prognosa.xml',
        'views/wika_tipe_jenis.xml',
        'data/loan_jenis.xml',
        'data/tipe_jenis.xml',
        'data/loan_stage.xml',
        'data/loan_allocation.xml',
        'views/wika_loan_stage.xml',
        'views/wika_loan_allocation.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
