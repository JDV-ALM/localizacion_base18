# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Account_move(models.Model):
    _inherit = 'account_move'
    

    # TODO: Migrar m�todos espec�ficos desde base_contable
    # TODO: Agregar validaciones espec�ficas de VE
    # TODO: Implementar l�gica de negocio
