from odoo import models, fields
from datetime import datetime, timedelta

class ApprovalWizard(models.TransientModel):
    _name = 'approval.wizard.account.move'
    _description = 'Approval Wizard'

    keterangan = fields.Html('Keterangan')
    # text = fields.Char('Text', readonly= True, default="Dengan ini Kami Menyatakan:\n1. Bahwa Menjamin dan Bertanggung Jawab Atas Kebenaran, Keabsahan Bukti Transaksi Beserta Bukti Pendukungnya, Dan Dokumen Yang Telah Di Upload Sesuai Dengan Aslinya\n2. Bahwa Mitra Kerja Tersebut telah melaksanakan pekerjaan Sebagaimana Yang Telah Dipersyaratkan di Dalam Kontrak, Sehingga Memenuhi Syarat Untuk Dibayar.\n\nCopy Dokumen Bukti Transaksi :\n- PO SAP\n- Dokumen Kontrak Lengkap\n- GR/SES\n- Surat Jalan (untuk material)\n- BAP\n- Invoice\n- Faktur Pajak")
    # is_cancelled = fields.Boolean(string="Is Cancelled", default=False)

    def ok(self):
        return {'type': 'ir.actions.act_window_close'}

    def cancel(self):
        return {'type': 'ir.actions.act_window_close'}