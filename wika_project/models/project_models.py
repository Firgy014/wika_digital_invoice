# -*- coding: utf-8 -*-

from odoo import models, fields, api



class projek(models.Model):
    _inherit = 'project.project'

    code        = fields.Char(string='Kode SPK', required = True,index=True)
    branch_id   = fields.Many2one(comodel_name='res.branch', string='Department',index=True)
    manager     = fields.Char(string='Manager')
    tender      = fields.Boolean(string='Tender?')
    is_jo       = fields.Boolean(string='Is Jo')
    lokasi      = fields.Char(string='Lokasi') # option: size=40, translate=False)
    omset       = fields.Char(string='Omset') # option: size=40, translate=False)
    kode_jurnal = fields.Char(string='Kode Jurnal') # option: size=40, translate=False)
    bank_id     = fields.Many2one(comodel_name='res.bank',
                              string="Bank", ondelete='set null', index=True)
    bank_partner_id = fields.Many2one(comodel_name='res.partner.bank',
                              string="Bank", ondelete='set null', index=True)

    manager_kasie_keu = fields.Char(string='Manager Kasie Keu') # option: size=40, translate=False)
    manager_kasie_kom = fields.Char(string='Manager Kasie Kom') # option: size=40, translate=False)
    manager_kasie_dan = fields.Char(string='Manager Kasie Dan') # option: size=40, translate=False)
    staff_keu = fields.Char(string='Staff Keu') # option: size=40, translate=False)
    staff_kom = fields.Char(string='Staff Kom') # option: size=40, translate=False)
    staff_dan = fields.Char(string='Staff Dan') # option: size=40, translate=False)
    
    isdivisi    = fields.Boolean(string='Is Wilayah')
    is_pmcs     = fields.Boolean(string='Is PMCS')
    id_spk      = fields.Char(string='ID SPK')
    termin      = fields.Many2one(comodel_name='account.payment.term', string='Termin')
    sap_code    = fields.Char(string="Kode SAP")


    def name_get(self):
        res = []
        for record in self:
            tit = "[%s] %s" % (record.code, record.name)
            res.append((record.id, tit))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=1000,name_get_uid=None):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            args = ['|', ('code', operator, name), ('name', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)

