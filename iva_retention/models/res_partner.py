# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError




class Partners(models.Model):
    _inherit = 'res.partner'

    #ret_agent = fields.Boolean(string='Retention agent', help='True if your partner is retention agent')
    purchase_jrl_id = fields.Many2one('account.journal', string='Purchase journal',company_dependent=True)
    sale_jrl_id = fields.Many2one('account.journal', string='Sales journal',company_dependent=True)
    ret_jrl_id = fields.Many2one('account.journal', string='Diario de Retenciones',company_dependent=True)
    vat_retention_rate = fields.Float(default=75)
    account_ret_receivable_id = fields.Many2one('account.account', string='Cuenta Retencion a Cobrar (Clientes)',company_dependent=True)
    account_ret_payable_id = fields.Many2one('account.account', string='Cuenta Retencion a Pagar (Proveedores)',company_dependent=True)


    @api.onchange('contribuyente')
    def actualiza_ctas_ret_iva(self):
    	if self.contribuyente=='si':
    		#self.ret_agent=True
    		self.ret_jrl_id=self.env.company.journal_ret_aux_id.id
    		self.account_ret_receivable_id=self.env.company.account_ret_receivable_aux_id.id
    		self.account_ret_payable_id=self.env.company.account_ret_payable_aux_id.id
    		if not self.vat_retention_rate:
    			self.vat_retention_rate=75