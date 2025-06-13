# -*- coding: utf-8 -*-
from odoo import api, models

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.model
    def _prepare_invoice_vals(self, order):
        """
        Parche para el wizard 'Crear factura' → 'Factura normal',
        forzando la factura a VES y convirtiendo cada price_unit
        desde la moneda de la orden (USD/EUR) a VES.
        """
        vals = super()._prepare_invoice_vals(order)
        ves = order.company_id.currency_id    # VES
        orig = order.currency_id              # USD/EUR u otra

        # 1) Forzar moneda VES
        vals['currency_id'] = ves.id

        # 2) Convertir cada línea de invoice_line_ids
        new_lines = []
        for cmd in vals.get('invoice_line_ids', []):
            if isinstance(cmd, (list, tuple)) and len(cmd) == 3 and isinstance(cmd[2], dict):
                pu = cmd[2].get('price_unit', 0.0)
                cmd[2]['price_unit'] = orig._convert(
                    pu, ves, order.company_id, order.date_order
                )
            new_lines.append(cmd)
        vals['invoice_line_ids'] = new_lines

        return vals
