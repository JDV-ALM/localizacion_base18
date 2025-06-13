# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Account_book_sales(models.Model):
    _inherit = 'account_book_sales'
    
    date_from = fields.Char(string='Date From')
    date_to = fields.Char(string='Date To')
    report_data = fields.Char(string='Report Data')

    # TODO: Migrar métodos específicos desde base_contable
    # TODO: Agregar validaciones específicas de VE
    # TODO: Implementar lógica de negocio
