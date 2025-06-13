# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Account_move(models.Model):
    _inherit = 'account_move'
    

    # TODO: Migrar métodos específicos desde base_contable
    # TODO: Agregar validaciones específicas de VE
    # TODO: Implementar lógica de negocio
