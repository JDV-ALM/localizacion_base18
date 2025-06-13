# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Isrl_retention(models.Model):
    _inherit = 'isrl_retention'
    
    name = fields.Char(string='Name')
    partner_id = fields.Char(string='Partner Id')
    date = fields.Char(string='Date')

    # TODO: Migrar métodos específicos desde base_contable
    # TODO: Agregar validaciones específicas de VE
    # TODO: Implementar lógica de negocio
