# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Isrl_retention(models.Model):
    _inherit = 'isrl_retention'
    
    name = fields.Char(string='Name')
    partner_id = fields.Char(string='Partner Id')
    date = fields.Char(string='Date')

    # TODO: Migrar m�todos espec�ficos desde base_contable
    # TODO: Agregar validaciones espec�ficas de VE
    # TODO: Implementar l�gica de negocio
