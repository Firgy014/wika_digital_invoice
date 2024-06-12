from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AmountSCFPriceCutModel(models.Model):
    _name = 'wika.amount.scf.wizard.ppr'
    
    partial_id = fields.Many2one('wika.partial.payment.request', string='Nomor Partial', default=lambda self: self.env.context.get('active_id'))
    amount = fields.Float(string='Nilai', required=True)
    posting_date = fields.Date(string='Posting Date', default=lambda self: fields.Date.context_today(self))

    def action_save(self):
        product_scf_id = self.env['product.product'].sudo().search([('name','=','Potongan SCF')], limit=1)

        if product_scf_id:
            self.env['wika.partial.pr.pricecut.line'].sudo().create({
                'partial_id': self.partial_id.id,
                'product_id': product_scf_id.id,
                'amount': self.amount,
                'posting_date': self.posting_date,
            })  
        return {'type': 'ir.actions.act_window_close'}
    
    # @api.constrains('amount')
    # def _check_amount(self):
    #     for record in self:
    #         if record.amount == 0.0:
    #             raise ValidationError(_("Potongan SCF harus lebih dari 0.0."))
    #         if record.amount > record.invoice_id.amount_invoice:
    #             raise ValidationError(_("Potongan SCF harus kurang dari amount Invoice."))
