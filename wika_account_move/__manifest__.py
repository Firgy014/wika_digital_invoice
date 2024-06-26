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
    'depends': ['base',
                'branch',
                'project',
                'account',
                'wika_berita_acara_pembayaran',
                'wika_matrix_approval'
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/scheduler.xml',
        'views/partner_views.xml',
        'views/setting_account_payable_views.xml',
        'views/product_views.xml',
        'views/wika_account_move.xml',
        'views/wika_account_move_line.xml',
        'views/doc_ap_non_po.xml',

        'views/account_tax_views.xml',
        'report/report_action.xml',
        # 'report/report_wika_account_move_divisi_divisi.xml',
        'report/report_wika_account_move_proyek.xml',
        'report/report_wika_account_move_keuangan.xml',
        'report/report_bap_progress.xml',
        'report/report_bap_uang_muka.xml',
        'report/report_bap_retensi.xml',
        'report/report_invoice_inherit.xml',
        'views/wika_special_gl.xml',
        'data/pricecut_scf_data.xml',
        'data/documents_folder_data.xml',
        'data/document_setting_data.xml',
        'data/special_gl.xml',
        'views/filter.xml',
        'views/action.xml',

        'wizard/wika_reject_reason.xml',
        'wizard/amount_scf.xml',
        'wizard/wika_approval_account_move.xml',

        'views/sequence_data.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
