# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools

class VendorBillsReport(models.Model):
    _name = 'wika.vendor.bills.report'
    _description = "Vendor Bills Pivot"
    _auto = False

    branch_id = fields.Many2one(comodel_name='res.branch', string='Divisi', readonly=True)
    biro = fields.Many2one(comodel_name='res.branch', string='Department', readonly=True)
    date_invoice = fields.Date(string='Tanggal', readonly=True)
    partner_id = fields.Many2one(comodel_name='res.partner',string='Vendor', readonly=True)
    tipe_budget = fields.Selection([('capex', 'Capex'), ('opex', 'Opex'),('bad','BAD')], string='Tipe Budget',readonly=True)
    is_beban = fields.Boolean(string='Pembebanan?',readonly=True)
    account_id = fields.Many2one(comodel_name='account.account',string='Kode COA',readonly=True)
    price_subtotal = fields.Float(string='Realisasi',readonly=True)
    form = fields.Char(string='Form',readonly=True)
    id_trx = fields.Integer(string='ID transaksi')
    nomor_budget = fields.Char(string='Nomor Budget',readonly=True)
    product_id = fields.Many2one(comodel_name='product.product',string='Product',readonly=True)
    parent_id = fields.Many2one(comodel_name='res.branch', string='Parent', readonly=True)

    # def init(self):
    #     tools.drop_view_if_exists(self._cr, 'report_invoice')
    #     self._cr.execute(
    #         """
    #             CREATE or REPLACE VIEW
    #                 wika_vendor_bills_report AS (
    #             SELECT
    #                 MIN(invl.id) AS id,
    #                 inv.branch_id,
    #                 inv.biro,
    #                 inv.date_invoice,
    #                 CASE WHEN
    #                     inv.is_beban = true AND
    #                     invl.partner_id_rk IS NOT NULL
    #                 THEN
    #                     invl.partner_id_rk
    #                 ELSE
    #                     inv.partner_id
    #                 END
    #                     AS partner_id,
    #                 inv.tipe_budget,
    #                 inv.is_beban,
    #                 invl.account_id AS account_id,
    #                 SUM(invl.price_subtotal) AS price_subtotal,
    #                 'Vendor Bills'::text AS form,
    #                 invl.invoice_id AS id_trx,
    #                 inv.nomor_budget,
    #                 invl.product_id,
    #                 CASE WHEN
    #                     branch.biro = true AND branch.parent_id IS NOT NULL THEN branch3.parent_id
    #                 WHEN
    #                     branch.biro <> true AND branch.parent_id IS NOT NULL THEN branch.parent_id
    #                 ELSE
    #                     branch.id
    #                 END
    #                     AS parent_id
    #             FROM
    #                 account_move_line invl
    #             LEFT JOIN
    #                 account_move inv ON invl.invoice_id = inv.id
    #             LEFT JOIN
    #                 res_branch branch ON inv.branch_id = branch.id
    #             LEFT JOIN
    #                 res_branch branch2 ON inv.biro = branch2.id
    #             LEFT JOIN
    #                 res_branch branch3 ON branch.parent_id = branch3.id
    #             LEFT JOIN
    #                 res_partner partner ON inv.partner_id = partner.id
    #             LEFT JOIN
    #                 account_account coa ON invl.account_id = coa.id
    #             WHERE
    #                 inv.type::text = 'in_invoice'::text
    #             GROUP BY
    #                 inv.branch_id, invl.invoice_id, inv.biro, inv.date_invoice, inv.partner_id, inv.tipe_budget, inv.is_beban, invl.partner_id_rk, invl.account_id,
    #                 inv.nomor_budget, invl.product_id, branch.id, branch.parent_id, branch3.parent_id
                
    #             UNION ALL
                
    #             SELECT
    #                 MIN(pay.id) AS id,
    #                 pay.branch_id,
    #                 pay.biro_id AS biro,
    #                 pay.date AS date_invoice,
    #                 pay.partner_id_rk AS partner_id,
    #                 'opex'::character varying AS tipe_budget,
    #                 true AS is_beban,
    #                 pay.account_id,
    #                 sum(pay.amount_subtotal) AS price_subtotal,
    #                 'Payroll'::text AS form,
    #                 pay.payroll_id AS id_trx,
    #                 payroll.nomor_budget,
	# 	            NULL as product_id,
    # 		        CASE WHEN
	# 		            branch.parent_id IS NOT NULL
	# 		        THEN 
	# 		            branch.parent_id
	# 	            ELSE
	# 		            branch.id
	# 	            END
	# 		            AS parent_id
    #             FROM
    #                 wika_payroll_line pay
    #             LEFT JOIN
    #                 wika_payroll payroll ON payroll.id = pay.payroll_id
    #             LEFT JOIN
    #                 res_branch branch ON pay.branch_id = branch.id
    #             LEFT JOIN
    #                 res_branch branch2 ON pay.biro_id = branch2.id
    #             LEFT JOIN
    #                 res_partner partner ON pay.partner_id = partner.id
    #             LEFT JOIN
    #                 account_account coa ON pay.account_id = coa.id
    #             GROUP BY
    #                 pay.branch_id, pay.payroll_id, pay.biro_id, pay.date, pay.partner_id_rk, true::boolean, pay.account_id, payroll.nomor_budget,branch.parent_id,branch.id
                
    #             UNION ALL
                
    #             SELECT
    #                 MIN(bad.id) AS id,
    #                 budget.department AS branch_id,
    #                 budget.biro,
    #                 budget.tanggal_bad AS date_invoice,
    #                 1 AS partner_id,
    #                 'bad'::character varying AS tipe_budget,
    #                 true AS is_beban,
    #                 bad.account_id,
    #                 sum(bad.total_anggaran) AS price_subtotal,
    #                 'BAD'::text AS form,
    #                 bad.coa_id AS id_trx,
    #                 budget.nomor_budget,
	# 	            bad.pekerjaan as product_id,
    #                 CASE WHEN
    #                     branch.parent_id  IS NOT NULL
    #                 THEN 
    #                     branch.parent_id
    #                 ELSE
    #                     branch.id
    #                 END
    #                     AS parent_id	
    #             FROM
    #                 wika_mcs_budget_coa_detail bad
    #             LEFT JOIN
    #                 wika_mcs_budget_coa budget ON budget.id = bad.coa_id
    #             LEFT JOIN
    #                 res_branch branch ON budget.department = branch.id
    #             LEFT JOIN
    #                 res_branch branch2 ON budget.biro = branch2.id
    #             LEFT JOIN
    #                 account_account coa ON bad.account_id = coa.id
    #             WHERE
    #                 budget.tipe_budget::text = 'bad'::text
    #             GROUP BY
    #                 bad.coa_id, budget.department, budget.biro, budget.tanggal_bad, budget.tipe_budget, bad.is_beban, bad.account_id, budget.nomor_budget,bad.pekerjaan,branch.parent_id,branch.id
                
    #             UNION ALL

    #             SELECT
    #                 MIN(rk.id) AS id,
    #                 rk.branch_id,
    #                 rk.biro_id AS biro,
    #                 rk.tanggal AS date_invoice,
    #                 rk.partner_id,
    #                 rk.tipe_budget,
    #                 false AS is_beban,
    #                 rk_line.account_id,
    #                 SUM(rk_line.amount) AS price_subtotal,
    #                 'Get RK'::text AS form,
    #                 rk_line.rk_id AS id_trx,
    #                 rk.nomor_budget,
    #                 rk_line.product_id as product_id,
    #                 CASE WHEN
    #                     branch.parent_id  IS NOT NULL
    #                 THEN 
    #                     branch.parent_id
    #                 ELSE
    #                     branch.id
    #                 END
    #                     AS parent_id
    #             FROM
    #                 wika_get_rk_line rk_line
    #             LEFT JOIN
    #                 get_rk rk ON rk.id = rk_line.rk_id
    #             LEFT JOIN
    #                 res_branch branch ON rk.branch_id = branch.id
    #             LEFT JOIN
    #                 res_branch branch2 ON rk.biro_id = branch2.id
    #             LEFT JOIN
    #                 res_partner partner ON rk.partner_id = partner.id
    #             LEFT JOIN
    #                 account_account coa ON rk_line.account_id = coa.id
    #             WHERE
    #                 rk.state::text = 'confirm'::text
    #             GROUP BY
    #                 rk.branch_id, rk_line.rk_id, rk.biro_id, rk.tanggal,
    #                 rk.partner_id, rk.tipe_budget, false::boolean, rk_line.account_id,
    #                 rk.nomor_budget,rk_line.product_id,branch.id,branch.parent_id
	
	#             UNION ALL
 
    #             SELECT
    #                 MIN(pc.id) AS id,
    #                 pc.branch_id,
    #                 pc.biro AS biro,
    #                 pc.date AS date_invoice,
    #                 pcl.partner_id,
    #                 'opex'::character varying AS tipe_budget,
    #                 false AS is_beban,
    #                 pcl.account_id,
    #                 sum(ABS(pcl.amount)) AS price_subtotal,
    #                 'Petty Cash'::text AS form,
    #                 pcl.statement_id AS id_trx,
    #                 pc.nomor_budget,
    #                 pcl.product_id,
    #                 CASE
    #                     WHEN branch.parent_id IS NOT NULL THEN branch.parent_id
    #                     ELSE branch.id
    #                 END AS parent_id
    #             FROM
    #                 account_bank_statement_line pcl
    #             LEFT JOIN
    #                 account_bank_statement pc ON pc.id = pcl.statement_id
    #             LEFT JOIN
    #                 res_branch branch ON pc.branch_id = branch.id
    #             LEFT JOIN
    #                 res_branch branch2 ON pc.biro = branch2.id
    #             LEFT JOIN
    #                 res_partner partner ON pcl.partner_id = partner.id
    #             LEFT JOIN
    #                 account_account coa ON pcl.account_id = coa.id
    #             WHERE
    #                 pc.is_petty_cash = true
    #             GROUP BY
    #                 pc.branch_id, pcl.statement_id, pc.biro, pc.date,
    #                 pcl.partner_id, pcl.account_id, pc.nomor_budget,
    #                 pcl.product_id, branch.id, branch.parent_id

	#             UNION ALL

    #             SELECT
    #                 MIN(pers.id) AS id,
    #                 pers.branch_id,
    #                 pers.biro AS biro,
    #                 pers.return_date AS date_invoice,
    #                 pers.partner_id,
    #                 'opex'::character varying AS tipe_budget,
    #                 false AS is_beban,
    #                 pers_line.account_id,
    #                 sum(pers_line.price_subtotal) AS price_subtotal,
    #                 'Persekot'::text AS form,
    #                 pers_line.loan_id AS id_trx,
    #                 pers.nomor_budget,
    #                 pers_line.product_id,
    #             CASE
    #                 WHEN branch.parent_id IS NOT NULL THEN branch.parent_id
    #                 ELSE branch.id
    #             END AS
    #                 parent_id
    #             FROM
    #                 employee_loan_details pers_line
    #             LEFT JOIN
    #                 employee_loan pers ON pers.id = pers_line.loan_id
    #             LEFT JOIN
    #                 res_branch branch ON pers.branch_id = branch.id
    #             LEFT JOIN
    #                 res_branch branch2 ON pers.biro = branch2.id
    #             LEFT JOIN
    #                 res_partner partner ON pers.partner_id = partner.id
    #             LEFT JOIN
    #                 account_account coa ON pers_line.account_id = coa.id
    #             GROUP BY
    #                 pers.branch_id, pers_line.loan_id, pers.biro, pers.return_date,
    #                 pers.partner_id, pers_line.account_id, pers.nomor_budget,
    #                 pers_line.product_id, branch.id, branch.parent_id
    # )
    #         """
    #     )
