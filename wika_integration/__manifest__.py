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
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','inherit_for_api','base_setup','wika_account_move','wika_payment_request'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data_url.xml',
        'data/scheduler.xml',
        'data/scheduler_generate_data.xml',
        'data/sap_configuration_data.xml',
        'views/wika_payment_request.xml',
        'views/sap_integration_views.xml',
        'views/configure_sap_integration_views.xml',
        'views/wika_integration_views.xml',
        'views/res_config_setting_views.xml',
        'views/wika_get_po.xml',
        'views/wika_get_gr.xml',
        'views/purchase_order.xml',
        'views/templates.xml',
        'views/account_payment_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}