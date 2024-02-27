from odoo import api, fields, models, _

class WikaTodoOverview(models.Model):
    _name = 'wika.todo.overview'
    _description = 'To Do Lists Overview'

    name = fields.Char(string='Name')
    kanban_type = fields.Selection([
        ('po', 'Purchase Orders'),
        ('grses', 'GR/SES'),
        ('bap', 'Berita Acara Pembayaran'),
        ('inv', 'Invoice'),
        ('pp', 'Pengajuan Pembayaran'),
    ], string='Type')
    fa_icon = fields.Selection([
        ('fa fa-file-text', 'PO Icon'),
        ('fa fa-archive', 'GR/SES Icon'),
        ('fa fa-files-o', 'BAP Icon'),
        ('fa fa-money', 'INVOICE Icon'),
        ('fa fa-credit-card', 'PR Icon'),
    ], string='Icon')
    
    count_po_total = fields.Char(compute='_compute_count_po_total', string='Total')
    count_po_to_upload = fields.Char(compute='_compute_count_po_to_upload', string='To Upload')
    count_po_to_approve = fields.Char(compute='_compute_count_po_to_approve', string='To Approve')
    count_po_late = fields.Char(compute='_compute_count_po_late', string='Late')

    count_grses_total = fields.Char(compute='_compute_count_grses_total', string='Total')
    count_grses_to_upload = fields.Char(compute='_compute_count_grses_to_upload', string='To Upload')
    count_grses_to_approve = fields.Char(compute='_compute_count_grses_to_approve', string='To Approve')
    count_grses_late = fields.Char(compute='_compute_count_grses_late', string='Late')

    count_bap_total = fields.Char(compute='_compute_count_bap_total', string='Total')
    count_bap_to_upload = fields.Char(compute='_compute_count_bap_to_upload', string='To Upload')
    count_bap_to_approve = fields.Char(compute='_compute_count_bap_to_approve', string='To Approve')
    count_bap_late = fields.Char(compute='_compute_count_bap_late', string='Late')

    count_inv_total = fields.Char(compute='_compute_count_inv_total', string='Total')
    count_inv_to_upload = fields.Char(compute='_compute_count_inv_to_upload', string='To Upload')
    count_inv_to_approve = fields.Char(compute='_compute_count_inv_to_approve', string='To Approve')
    count_inv_late = fields.Char(compute='_compute_count_inv_late', string='Late')

    count_pp_total = fields.Char(compute='_compute_count_pp_total', string='Total')
    count_pp_to_upload = fields.Char(compute='_compute_count_pp_to_upload', string='To Upload')
    count_pp_to_approve = fields.Char(compute='_compute_count_pp_to_approve', string='To Approve')
    count_pp_late = fields.Char(compute='_compute_count_pp_late', string='Late')

    # ============================= PURCHASE ORDER =============================
    
    def _compute_count_po_total(self):
        po_total = self.env['purchase.order'].sudo().search_count([('state', 'in', ['po','uploaded','approved'])])
        if isinstance(po_total, int):
            self.count_po_total = po_total

    def _compute_count_po_to_upload(self):
        po_to_upload = self.env['mail.activity'].sudo().search_count([
            ('status', '=', 'todo'),
            ('res_model', '=', 'purchase.order'),
        ])
        if isinstance(po_to_upload, int):
            self.count_po_to_upload = po_to_upload

    def _compute_count_po_to_approve(self):
        po_to_approve = self.env['mail.activity'].sudo().search_count([
            ('status', '=', 'to_approve'),
            ('res_model', '=', 'purchase.order'),
        ])
        if isinstance(po_to_approve, int):
            self.count_po_to_approve = po_to_approve

    def _compute_count_po_late(self):
        po_late = self.env['mail.activity'].sudo().search_count([
            ('state', '=', 'overdue'),
            ('res_model', '=', 'purchase.order'),
        ])
        if isinstance(po_late, int):
            self.count_po_late = po_late


    # ============================= GR/SES =============================

    def _compute_count_grses_total(self):
        grses_total = self.env['stock.picking'].sudo().search_count([('state', 'in', ['waits','uploaded','approved'])])
        if isinstance(grses_total, int):
            self.count_grses_total = grses_total

    def _compute_count_grses_to_upload(self):
        grses_to_upload = self.env['mail.activity'].sudo().search_count([
            ('status', '=', 'todo'),
            ('res_model', '=', 'stock.picking'),
        ])
        if isinstance(grses_to_upload, int):
            self.count_grses_to_upload = grses_to_upload

    def _compute_count_grses_to_approve(self):
        grses_to_approve = self.env['mail.activity'].sudo().search_count([
            ('status', '=', 'to_approve'),
            ('res_model', '=', 'stock.picking'),
        ])
        if isinstance(grses_to_approve, int):
            self.count_grses_to_approve = grses_to_approve

    def _compute_count_grses_late(self):
        grses_late = self.env['mail.activity'].sudo().search_count([
            ('state', '=', 'overdue'),
            ('res_model', '=', 'stock.picking'),
        ])
        if isinstance(grses_late, int):
            self.count_grses_late = grses_late


    # ============================= BERITA ACARA PEMBAYARAN =============================

    def _compute_count_bap_total(self):
        bap_total = self.env['wika.berita.acara.pembayaran'].sudo().search_count([('state', 'in', ['draft','uploaded','approved'])])
        if isinstance(bap_total, int):
            self.count_bap_total = bap_total

    def _compute_count_bap_to_upload(self):
        bap_to_upload = self.env['mail.activity'].sudo().search_count([
            ('status', '=', 'todo'),
            ('res_model', '=', 'wika.berita.acara.pembayaran'),
        ])
        if isinstance(bap_to_upload, int):
            self.count_bap_to_upload = bap_to_upload

    def _compute_count_bap_to_approve(self):
        bap_to_approve = self.env['mail.activity'].sudo().search_count([
            ('status', '=', 'to_approve'),
            ('res_model', '=', 'wika.berita.acara.pembayaran'),
        ])
        if isinstance(bap_to_approve, int):
            self.count_bap_to_approve = bap_to_approve

    def _compute_count_bap_late(self):
        bap_late = self.env['mail.activity'].sudo().search_count([
            ('state', '=', 'overdue'),
            ('res_model', '=', 'wika.berita.acara.pembayaran'),
        ])
        if isinstance(bap_late, int):
            self.count_bap_late = bap_late


    # ============================= INVOICE =============================

    def _compute_count_inv_total(self):
        inv_total = self.env['account.move'].sudo().search_count([('state', 'in', ['draft','uploaded','approved'])])
        if isinstance(inv_total, int):
            self.count_inv_total = inv_total

    def _compute_count_inv_to_upload(self):
        inv_to_upload = self.env['mail.activity'].sudo().search_count([
            ('status', '=', 'todo'),
            ('res_model', '=', 'account.move'),
        ])
        if isinstance(inv_to_upload, int):
            self.count_inv_to_upload = inv_to_upload

    def _compute_count_inv_to_approve(self):
        inv_to_approve = self.env['mail.activity'].sudo().search_count([
            ('status', '=', 'to_approve'),
            ('res_model', '=', 'account.move'),
        ])
        if isinstance(inv_to_approve, int):
            self.count_inv_to_approve = inv_to_approve

    def _compute_count_inv_late(self):
        inv_late = self.env['mail.activity'].sudo().search_count([
            ('state', '=', 'overdue'),
            ('res_model', '=', 'account.move'),
        ])
        if isinstance(inv_late, int):
            self.count_inv_late = inv_late


    # ============================= PAYMENT REQUEST =============================

    def _compute_count_pp_total(self):
        pp_total = self.env['wika.payment.request'].sudo().search_count([('state', 'in', ['draft','request','approve','reject'])])
        if isinstance(pp_total, int):
            self.count_pp_total = pp_total

    def _compute_count_pp_to_upload(self):
        pp_to_upload = self.env['mail.activity'].sudo().search_count([
            ('status', '=', 'todo'),
            ('res_model', '=', 'wika.payment.request'),
        ])
        if isinstance(pp_to_upload, int):
            self.count_pp_to_upload = pp_to_upload

    def _compute_count_pp_to_approve(self):
        pp_to_approve = self.env['mail.activity'].sudo().search_count([
            ('status', '=', 'to_approve'),
            ('res_model', '=', 'wika.payment.request'),
        ])
        if isinstance(pp_to_approve, int):
            self.count_pp_to_approve = pp_to_approve

    def _compute_count_pp_late(self):
        pp_late = self.env['mail.activity'].sudo().search_count([
            ('state', '=', 'overdue'),
            ('res_model', '=', 'wika.payment.request'),
        ])
        if isinstance(pp_late, int):
            self.count_pp_late = pp_late


    # ============================= ACTION TOTAL =============================

    def action_method_total(self):

        if self.kanban_type == 'po':
            self.ensure_one()
            act_name = 'All Purchase Orders in Digital Invoicing'
            res_model = 'purchase.order'
            view_tree_id = self.env.ref("wika_purchase.purchase_order_tree_wika", raise_if_not_found=False)
            view_form_id = self.env.ref("wika_purchase.purchase_order_form_wika", raise_if_not_found=False)
            domain = ['po','uploaded','approved']

        elif self.kanban_type == 'grses':
            self.ensure_one()
            act_name = 'All GR/SES in Digital Invoicing'
            res_model = 'stock.picking'
            view_tree_id = self.env.ref("wika_inventory.stock_picking_tree_wika", raise_if_not_found=False)
            view_form_id = self.env.ref("wika_inventory.stock_picking_form_wika", raise_if_not_found=False)
            domain = ['waits','uploaded','approved']
            
        elif self.kanban_type == 'bap':
            self.ensure_one()
            act_name = 'All Berita Acara Pembayaran in Digital Invoicing'
            res_model = 'wika.berita.acara.pembayaran'
            view_tree_id = self.env.ref("wika_berita_acara_pembayaran.wika_berita_acara_pembayaran_view_tree", raise_if_not_found=False)
            view_form_id = self.env.ref("wika_berita_acara_pembayaran.wika_berita_acara_pembayaran_view_form", raise_if_not_found=False)
            domain = ['draft','uploaded','approved']

        elif self.kanban_type == 'inv':
            self.ensure_one()
            act_name = 'All Invoice in Digital Invoicing'
            res_model = 'account.move'
            view_tree_id = self.env.ref("wika_account_move.view_wika_account_move_tree_inherited", raise_if_not_found=False)
            view_form_id = self.env.ref("wika_account_move.view_wika_account_move", raise_if_not_found=False)
            domain = ['draft','uploaded','approved']

        elif self.kanban_type == 'pp':
            self.ensure_one()
            act_name = 'All Pengajuan Pembayaran in Digital Invoicing'
            res_model = 'wika.payment.request'
            view_tree_id = self.env.ref("wika_payment_request.wika_payment_request_view_tree", raise_if_not_found=False)
            view_form_id = self.env.ref("wika_payment_request.wika_payment_request_view_form", raise_if_not_found=False)
            domain = ['draft','request','approve','reject']

        return {
            'name': _(act_name),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': res_model,
            'view_ids': [(view_tree_id, 'tree'), (view_form_id, 'form')],
            'domain': [('state', 'in', domain)],  
        }

    # ============================= ACTION TO UPLOAD =============================

    def action_method_to_upload(self):
        self.ensure_one()
        view_tree_id = self.env.ref("wika_dashboard.mail_activity_todo_view_tree", raise_if_not_found=False)
        view_form_id = self.env.ref("wika_dashboard.mail_activity_todo_view_form", raise_if_not_found=False)

        if self.kanban_type == 'po':
            act_name = 'Purchase Orders to Upload'
            res_model = 'purchase.order'

        elif self.kanban_type == 'grses':
            act_name = 'GR/SES to Upload'
            res_model = 'stock.picking'
            
        elif self.kanban_type == 'bap':
            act_name = 'Berita Acara Pembayaran to Upload'
            res_model = 'wika.berita.acara.pembayaran'

        elif self.kanban_type == 'inv':
            act_name = 'Invoice to Upload'
            res_model = 'account.move'

        elif self.kanban_type == 'pp':
            act_name = 'Pengajuan Pembayaran to Request'
            res_model = 'wika.payment.request'

        return {
            'name': _(act_name),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'mail.activity',
            'view_ids': [(view_tree_id, 'tree'), (view_form_id, 'form')],
            'res_id': self.id,
            'domain': [('status', '=', 'todo'), ('res_model', '=', res_model)],  
        }
    

    # ============================= ACTION TO APPROVE =============================

    def action_method_to_approve(self):
        self.ensure_one()
        view_tree_id = self.env.ref("wika_dashboard.mail_activity_todo_view_tree", raise_if_not_found=False)
        view_form_id = self.env.ref("wika_dashboard.mail_activity_todo_view_form", raise_if_not_found=False)

        if self.kanban_type == 'po':
            act_name = 'Purchase Orders to Approve'
            res_model = 'purchase.order'

        elif self.kanban_type == 'grses':
            act_name = 'GR/SES to Approve'
            res_model = 'stock.picking'
            
        elif self.kanban_type == 'bap':
            act_name = 'Berita Acara Pembayaran to Approve'
            res_model = 'wika.berita.acara.pembayaran'

        elif self.kanban_type == 'inv':
            act_name = 'Invoice to Approve'
            res_model = 'account.move'

        elif self.kanban_type == 'pp':
            act_name = 'Pengajuan Pembayaran to Approve'
            res_model = 'wika.payment.request'

        return {
            'name': _(act_name),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'mail.activity',
            'view_ids': [(view_tree_id, 'tree'), (view_form_id, 'form')],
            'res_id': self.id,
            'domain': [('status', '=', 'todo'), ('res_model', '=', res_model)],  
        }


    # ============================= ACTION LATE =============================

    def action_method_late(self):
        self.ensure_one()
        view_tree_id = self.env.ref("wika_dashboard.mail_activity_todo_view_tree", raise_if_not_found=False)
        view_form_id = self.env.ref("wika_dashboard.mail_activity_todo_view_form", raise_if_not_found=False)

        if self.kanban_type == 'po':
            act_name = 'Expired Purchase Orders'
            res_model = 'purchase.order'

        elif self.kanban_type == 'grses':
            act_name = 'Expired GR/SES'
            res_model = 'stock.picking'
            
        elif self.kanban_type == 'bap':
            act_name = 'Expired Berita Acara Pembayaran'
            res_model = 'wika.berita.acara.pembayaran'

        elif self.kanban_type == 'inv':
            act_name = 'Expired Invoice to Upload'
            res_model = 'account.move'

        elif self.kanban_type == 'pp':
            act_name = 'Expired Pengajuan Pembayaran'
            res_model = 'wika.payment.request'

        return {
            'name': _(act_name),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'mail.activity',
            'view_ids': [(view_tree_id, 'tree'), (view_form_id, 'form')],
            'res_id': self.id,
            'domain': [('status', '=', 'todo'), ('res_model', '=', res_model)],  
        }
