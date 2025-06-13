# -*- coding: utf-8 -*-
from odoo import models

class AccountMove(models.Model):
    _inherit = 'account.move'

    def valida_pagos_progra(self):
        # anulamos la validación para que no requiera registros de pago antes de confirmar
        return True
