from odoo import models, fields, api
from datetime import datetime, timedelta

class WikaBeritaAcaraPembayaran(models.Model):
    _name = 'wika.berita.acara.pembayaran'
    _description = 'Berita Acara Pembayaran'

    name = fields.Char(string='Nomor BAP', readonly=True, default='/')
    branch_id = fields.Many2one('res.branch', string='Divisi')
    department_id = fields.Many2one('res.branch', string='Department')
    project_id = fields.Many2one('project.project', string='Project')
    po_id = fields.Many2one('purchase.order', string='Nomor PO', domain="[('state', '=', 'purchase')]")
    partner_id = fields.Many2one('res.partner', string='Vendor')
    bap_ids = fields.One2many('wika.berita.acara.pembayaran.line', 'bap_id', string='List BAP')
    document_ids = fields.One2many('wika.bap.document.line', 'bap_id', string='List Document')
    history_approval_ids = fields.One2many('wika.bap.approval.line', 'bap_id', string='List Approval')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    state = fields.Selection([('draft', 'Draft'), ('upload', 'Upload'), ('approve', 'Approve'), ('reject', 'Reject')], string='Status', readonly=True, default='draft')
    reject_reason = fields.Text(string='Reject Reason')
    step_approve = fields.Integer(string='step approve')

    # @api.model
    # def create(self, vals):
    #     res = super(WikaBeritaAcaraPembayaran, self).create(vals)

        
    #     return res

    def action_reject(self):
        action = self.env.ref('wika_berita_acara_pembayaran.action_reject_wizard').read()[0]
        
        return action

    def action_submit(self):
        self.write({'state': 'upload'})

    def action_approve(self):
        active_id = self.env.context.get('active_id')
        # print("TESTTTTT" , active_id)
        if active_id:
            audit_log_obj = self.env['wika.bap.approval.line'].create({'user_id': self._uid,
                # 'groups_id' :groups_id.id,
                'date': datetime.now(),
                # 'description': 'Approve',
                # 'level': 'Department',
                'bap_id': self.active_id
                })
            # return {'type': 'ir.actions.act_window_close'}
        self.write({'state': 'approve'})
      
    def action_cancel(self):
        self.write({'state': 'draft'})
      
    # def action_reject(self):
    #     self.write({'state': 'reject'})
        
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('wika.berita.acara.pembayaran')
        return super(WikaBeritaAcaraPembayaran, self).create(vals)

    @api.onchange('po_id')
    def onchange_po(self):
        self.partner_id = self.po_id.partner_id.id

class WikaBeritaAcaraPembayaranLine(models.Model):
    _name = 'wika.berita.acara.pembayaran.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    picking_id = fields.Many2one('stock.picking', string='NO GR/SES')
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Integer(string='Quantity')
    tax_ids = fields.Many2many('account.tax', string='Tax')
    currency_id = fields.Many2one('res.currency', string='Currency')
    unit_price = fields.Monetary(string='Unit Price')
    sub_total = fields.Monetary(string='Subtotal')

class WikaBabDocumentLine(models.Model):
    _name = 'wika.bap.document.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    document_id = fields.Many2one('wika.document.setting', string='Document')
    document = fields.Binary(string="Upload File", attachment=True, store=True)
    filename = fields.Char(string="File Name")
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('uploaded', 'Uploaded'),
        ('verif', 'Verif'),
    ], string='Status', default='waiting')

class WikaBabApprovalLine(models.Model):
    _name = 'wika.bap.approval.line'

    bap_id = fields.Many2one('wika.berita.acara.pembayaran', string='')
    user_id = fields.Many2one('res.users', string='User')
    groups_id = fields.Many2one('res.groups', string='Groups')
    datetime = fields.Datetime('Date')
    note = fields.Char('Note')
