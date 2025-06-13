# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Res_company(models.Model):
    _inherit = 'res_company'
    

    # TODO: Migrar métodos específicos desde base_contable
    # TODO: Agregar validaciones específicas de VE
    # TODO: Implementar lógica de negocio
