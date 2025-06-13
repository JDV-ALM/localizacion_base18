# -*- coding: utf-8 -*-
from odoo import api, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        """
        Se llama siempre que se crea una factura normal (botón 'Crear factura')
        Forzamos la factura a VES y convertimos los price_unit de las líneas.
        """
        invoice_vals = super()._prepare_invoice()
        ves = self.company_id.currency_id      # VES
        orig = self.currency_id                # USD/EUR u otra
        invoice_vals['currency_id'] = ves.id

        new_lines = []
        for cmd in invoice_vals.get('invoice_line_ids', []):
            if isinstance(cmd, (list, tuple)) and len(cmd) == 3 and isinstance(cmd[2], dict):
                pu = cmd[2].get('price_unit', 0.0)
                cmd[2]['price_unit'] = orig._convert(
                    pu, ves, self.company_id, self.date_order
                )
            new_lines.append(cmd)
        invoice_vals['invoice_line_ids'] = new_lines

        return invoice_vals

    def _create_invoices(self, grouped=False, final=False):
        """
        Se llama desde el wizard de 'Pago anticipado' (y cualquier otro flujo _create_invoices).
        Aquí volvemos a forzar VES y convertir unitarios antes de recomputar impuestos.
        """
        moves = super()._create_invoices(grouped=grouped, final=final)
        ves = self.company_id.currency_id
        for order, move in zip(self, moves):
            # Solo facturas cliente/proveedor
            if move.move_type in ('out_invoice', 'in_invoice') and move.currency_id != ves:
                orig = order.currency_id
                date = order.date_order
                for line in move.invoice_line_ids:
                    line.price_unit = orig._convert(
                        line.price_unit, ves, order.company_id, date
                    )
                move.currency_id = ves
                # Recalcular impuestos y totales dinámicos
                move._recompute_tax_lines()
                move._compute_amount()
        return moves
