# -*- coding: utf-8 -*-


import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError




class ResCompany(models.Model):
    _inherit = 'res.company'

    account_ret_receivable_aux_id = fields.Many2one('account.account',company_dependent=True)
    account_ret_payable_aux_id = fields.Many2one('account.account',company_dependent=True)
    journal_ret_aux_id = fields.Many2one('account.journal',company_dependent=True)
   