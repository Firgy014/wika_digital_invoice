# -*- coding: utf-8 -*-
{
    'name': "wika_berita_acara_pembayaran",

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
    'depends': ['base','branch','project', 'purchase','stock','product', 'account', 'wika_matrix_approval', 'wika_purchase', 'wika_inventory'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/documents_folder_data.xml',
        'views/wika_berita_acara_pembayaran.xml',
        'report/report_action.xml',
        'report/report_wika_berita_acara_pembayaran.xml',
        'report/report_wika_berita_acara_pembayaran_uang_muka.xml',
        'report/report_wika_berita_acara_pembayaran_retensi.xml',
        'report/report_wika_berita_acara_pembayaran_cut_over.xml',
        'views/sequence_data.xml',
        'views/wika_menu.xml',
        'wizard/wika_reject_reason.xml',

    ],
    
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wika_berita_acara_pembayaran/static/src/js/**/*.js',
            'wika_berita_acara_pembayaran/static/src/xml/**/*.xml',
        ],
    },
}
