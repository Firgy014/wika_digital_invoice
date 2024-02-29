# -*- coding: utf-8 -*-
{
    'name': "WiKA Integration",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Matrica",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','inherit_for_api','base_setup','wika_account_move'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data_url.xml',
        'views/sap_integration_views.xml',
        'views/wika_integration_views.xml',
        'views/res_config_setting_views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}