# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Isrl_retention_line(models.Model):
    _inherit = 'isrl_retention_line'
    
    retention_id = fields.Char(string='Retention Id')
    concept_id = fields.Char(string='Concept Id')
    amount = fields.Char(string='Amount')

    # TODO: Migrar métodos específicos desde base_contable
    # TODO: Agregar validaciones específicas de VE
    # TODO: Implementar lógica de negocio
