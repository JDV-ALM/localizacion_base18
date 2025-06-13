# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def alert_views(self):
        # Obtiene salidas de inventario (guías) hechas por ventas sin factura
        pickings = self.search([
            ('picking_type_code', '=', 'outgoing'),
            ('state', '=', 'done'),
            ('sale_id', '!=', False),
            ('sale_id.invoice_count', '=', 0),
        ])
        count = len(pickings)
        if count > 0:
            hoy = date.today().strftime('%d-%m-%Y')
            return _(
                'Tienes %d guías de despacho sin facturar al %s. '
                'De facturarse en el siguiente periodo el Seniat será Notificado.'
            ) % (count, hoy)
        return False