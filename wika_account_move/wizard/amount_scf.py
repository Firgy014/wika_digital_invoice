from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AmountSCFPriceCutModel(models.Model):
    _name = 'wika.amount.scf.wizard'
    
    invoice_id = fields.Many2one('account.move', string='Invoice', default=lambda self: self.env.context.get('active_id'))
    amount = fields.Float(string='Nilai', required=True)
    posting_date = fields.Date(string='Posting Date', default=lambda self: fields.Date.context_today(self))

    # @api.onchange('posting_date')
    # def _onchange_posting_date(self):
    #     if self.invoice_id.bap_id:
    #         if self.posting_date < self.invoice_id.bap_id.bap_date:
    #             raise ValidationError("Posting Date untuk Potongan SCF harus lebih atau sama dengan Tanggal BAP yang dipilih.")

    def action_save(self):
        product_scf_id = self.env['product.product'].sudo().search([('name','=','Potongan SCF')], limit=1)

        if product_scf_id:
            self.env['wika.account.move.pricecut.line'].sudo().create({
                'move_id': self.invoice_id.id,
                'product_id': product_scf_id.id,
                'amount': self.amount,
                'posting_date': self.posting_date,
            })  
        return {'type': 'ir.actions.act_window_close'}
    
    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount == 0.0:
                raise ValidationError(_("Potongan SCF harus lebih dari 0.0."))
            if record.amount > record.invoice_id.amount_invoice:
                raise ValidationError(_("Potongan SCF harus kurang dari amount Invoice."))
