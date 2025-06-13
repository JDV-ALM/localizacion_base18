# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LibroInventarioWizard(models.TransientModel):
    _name = 'libro.inventario.wizard'
    _description = 'Wizard para generar el Libro de Inventario'

    date_from = fields.Date(string='Desde', required=True)
    date_to   = fields.Date(string='Hasta', required=True)
    line_ids  = fields.One2many(
        'libro.inventario.wizard.line', 'wizard_id',
        string='Líneas', readonly=True
    )

    def compute_lines(self):
        # 1) Limpiamos las líneas anteriores
        self.line_ids.unlink()
        SL = self.env['stock.valuation.layer']

        # 2) Definimos dominios
        domain_before = [
            ('create_date', '<',  self.date_from),
            ('company_id',  '=', self.env.company.id),
        ]
        domain_period = [
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('company_id',  '=', self.env.company.id),
        ]
        sum_fields   = ['quantity', 'value']
        group_fields = ['product_id']

        # 3) Existencia inicial (hasta date_from)
        before = {
            rec['product_id'][0]: rec
            for rec in SL.read_group(domain_before, sum_fields, group_fields)
        }

        # 4) Movimientos del período: Entradas y Salidas por separado
        entries = {
            rec['product_id'][0]: rec
            for rec in SL.read_group(domain_period + [('quantity', '>', 0)], sum_fields, group_fields)
        }
        exits = {
            rec['product_id'][0]: rec
            for rec in SL.read_group(domain_period + [('quantity', '<', 0)], sum_fields, group_fields)
        }

        # 5) Recopilamos todos los productos involucrados
        product_ids = set(before) | set(entries) | set(exits)

        for pid in product_ids:
            prod = self.env['product.product'].browse(pid)
            bi = before.get(pid, {'quantity': 0.0, 'value': 0.0})
            ed = entries.get(pid, {'quantity': 0.0, 'value': 0.0})
            xd = exits.get(pid,   {'quantity': 0.0, 'value': 0.0})

            # — Existencia Inicial —
            initial_qty   = bi['quantity']
            initial_total = bi['value']
            initial_cost  = (initial_total / initial_qty) if initial_qty else 0.0
            # Fallback al standard_price si no hay value
            if initial_qty and not initial_total:
                initial_cost  = prod.standard_price
                initial_total = initial_qty * prod.standard_price

            # — Entradas del mes —
            entries_qty   = ed['quantity']
            entries_total = ed['value']
            entries_cu    = (entries_total / entries_qty) if entries_qty else 0.0
            # Fallback a precio de proveedor o standard_price
            if entries_qty and not entries_total:
                price_unit = prod.seller_ids[:1].price or prod.standard_price
                entries_cu    = price_unit
                entries_total = entries_qty * price_unit

            # — Salidas del mes —
            exits_qty = abs(xd['quantity'])
            exits_total = abs(xd['value'])
            if exits_qty:
                if exits_total > 0:
                    # usamos valor real
                    exits_cu = exits_total / exits_qty
                else:
                    # fallback a costo inicial o standard_price
                    exits_cu = initial_cost if initial_cost > 0 else prod.standard_price
                exits_total = exits_qty * exits_cu
            else:
                exits_cu = 0.0
                exits_total = 0.0

            # — Inventario Final y Costo Promedio —
            final_stock = initial_qty + entries_qty - exits_qty
            final_total = initial_total + entries_total - exits_total
            avg_cost    = (final_total / final_stock) if final_stock else 0.0

            # Creamos la línea del wizard
            self.env['libro.inventario.wizard.line'].create({
                'wizard_id':           self.id,
                'code':                prod.default_code or '',
                'unit':                prod.uom_id.name or '',
                'description':         prod.name or '',
                'initial_qty':         initial_qty,
                'initial_cost':        initial_cost,
                'initial_total':       initial_total,
                'entries':             entries_qty,
                'entries_cost_unit':   entries_cu,
                'entries_total':       entries_total,
                'exits':               exits_qty,
                'exits_cost_unit':     exits_cu,
                'exits_total':         exits_total,
                'final_stock':         final_stock,
                'average_cost':        avg_cost,
                'final_total':         final_total,
            })

    def print_report(self):
        self.ensure_one()
        self.compute_lines()
        return self.env.ref(
            'libro_inventario.report_libro_inventario_action'
        ).report_action(self)
