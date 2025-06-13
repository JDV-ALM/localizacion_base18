from odoo import models, fields, api
from .currency_rate_fetcher import obtener_tasa_bcv  # Importa la función de otro archivo

class CurrencyRateUpdater(models.Model):
    _name = 'currency_rate_updater'  # Nombre correcto
    _description = 'Actualiza la tasa del dólar desde el BCV'

    @api.model
    def actualizar_tasa_odoo(self):
        tasa, fecha = obtener_tasa_bcv()
        if not tasa:
            return

        currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if currency:
            self.env['res.currency.rate'].create({
                'currency_id': currency.id,
                'rate': 1 / tasa,
                'name': fecha
            })