# -*- coding: utf-8 -*-
{
    'name': "Wika Dashboard",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Andromeda",
    'website': "https://andromedasupendi.pythonanywhere.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','web','wika_activity','documents'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/kanban_data.xml',
        'views/dashboard_todo_views.xml',
        'views/dashboard_document_views.xml',
        'views/todo_overview_views.xml',
        'views/action.xml',
        'views/menu.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wika_dashboard/static/src/js/dashboard.js',
        ],
    },
}
