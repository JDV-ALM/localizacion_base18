# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Vat_retention_line(models.Model):
    _inherit = 'vat_retention_line'
    
    retention_id = fields.Char(string='Retention Id')
    invoice_id = fields.Char(string='Invoice Id')
    base_amount = fields.Char(string='Base Amount')

    # TODO: Migrar métodos específicos desde base_contable
    # TODO: Agregar validaciones específicas de VE
    # TODO: Implementar lógica de negocio
