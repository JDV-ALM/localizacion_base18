# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Account_payment_fact(models.Model):
    _inherit = 'account_payment_fact'
    

    # TODO: Migrar métodos específicos desde base_contable
    # TODO: Agregar validaciones específicas de VE
    # TODO: Implementar lógica de negocio
