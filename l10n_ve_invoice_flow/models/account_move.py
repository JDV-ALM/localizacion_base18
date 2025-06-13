# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    pago_divisas = fields.Boolean(string="Pago en Divisas")
    amount_igtf = fields.Monetary(string="Impuesto IGTF", compute="_compute_igtf")

    @api.model_create_multi
    def create(self, vals_list):
        """
        1) Crear la factura (vía wizard o botón normal).
        2) Detectar si procede de una sale.order o purchase.order.
        3) Convertir cada línea price_unit de esa moneda → VES.
        4) Forzar currency_id = VES y recalcular impuestos/totales.
        """
        moves = super().create(vals_list)
        for move in moves.filtered(lambda m: m.move_type in ('out_invoice', 'in_invoice')):
            # 1) Obtener la currency original: sale.order o purchase.order
            orig_cur = False
            if move.invoice_origin:
                so = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
                if so:
                    orig_cur = so.currency_id
                else:
                    po = self.env['purchase.order'].search([('name', '=', move.invoice_origin)], limit=1)
                    orig_cur = po.currency_id if po else False
            # 2) Moneda local de la compañía (VES)
            ves = move.company_id.currency_id
            # 3) Si la moneda original existe y es distinta de VES, convertir
            if orig_cur and orig_cur != ves:
                inv_date = move.invoice_date or move.date
                for line in move.invoice_line_ids:
                    pu = line.price_unit
                    new_pu = orig_cur._convert(pu, ves, move.company_id, inv_date)
                    _logger.info("→ Convirtiendo %s %s → %s %s", pu, orig_cur.name, new_pu, ves.name)
                    line.price_unit = new_pu
                move.currency_id = ves.id
                # 4) Recalcular dinámicos y totales
                move._recompute_dynamic_lines()
                move._compute_amount()
        return moves

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        # Anular recálculo automático que pudiera pisar los price_unit
        return {}

    def _recompute_dynamic_lines(self):
        # Anular lógica dinámica heredada que vuelva a pisar precios
        return

    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.is_igtf_line')
    def _compute_igtf(self):
        for move in self:
            move.amount_igtf = sum(
                l.price_subtotal for l in move.invoice_line_ids
                if getattr(l, 'is_igtf_line', False)
            )

    def action_post(self):
        """
        Inserta la línea de IGTF si:
         - El usuario marcó Pago en Divisas (pago_divisas=True)
         - Usa el mismo % para ventas y compras
         - Apunta a la cuenta configurada para clientes o proveedores
        """
        for move in self:
            if not move.pago_divisas:
                continue

            # Seleccionar cuenta y % según tipo de documento
            if move.is_sale_document():
                igtf_acc = move.company_id.account_igtf_id
                pct = move.company_id.percentage_cli_igtf or 0.0
            else:
                igtf_acc = move.company_id.account_igtf_p_id
                pct = move.company_id.percentage_cli_igtf or 0.0

            if not igtf_acc:
                raise UserError(_("Configure la cuenta IGTF en la ficha de la compañía."))

            # Eliminar líneas IGTF anteriores
            old = move.invoice_line_ids.filtered(
                lambda l: getattr(l, 'is_igtf_line', False) or l.account_id == igtf_acc
            )
            if old:
                old.unlink()

            # Calcular base imponible sin IGTF
            base = sum(
                l.price_subtotal for l in move.invoice_line_ids
                if not (getattr(l, 'is_igtf_line', False) or l.account_id == igtf_acc)
            )
            amt = base * pct / 100.0
            if amt:
                move.write({
                    'invoice_line_ids': [(0, 0, {
                        'name': _("IGTF %s%%") % pct,
                        'quantity': 1.0,
                        'price_unit': amt,
                        'account_id': igtf_acc.id,
                        'is_igtf_line': True,
                    })]
                })

        return super().action_post()
