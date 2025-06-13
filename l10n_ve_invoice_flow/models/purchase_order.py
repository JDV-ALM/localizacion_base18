# -*- coding: utf-8 -*-
from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _prepare_invoice(self):
        """
        Forzamos la factura de compra a moneda VES y convertimos precios de línea
        desde la moneda de la orden de compra a VES.
        """
        invoice_vals = super()._prepare_invoice()
        ves = self.company_id.currency_id
        orig = self.currency_id
        invoice_vals['currency_id'] = ves.id

        new_lines = []
        for cmd in invoice_vals.get('invoice_line_ids', []):
            if isinstance(cmd, (list, tuple)) and len(cmd) == 3 and isinstance(cmd[2], dict):
                vals = cmd[2]
                pu = vals.get('price_unit', 0.0)
                vals['price_unit'] = orig._convert(
                    pu, ves, self.company_id,
                    self.date_order or fields.Date.context_today(self)
                )
            new_lines.append(cmd)
        invoice_vals['invoice_line_ids'] = new_lines

        return invoice_vals
