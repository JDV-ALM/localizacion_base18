# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

### 1) Convierte siempre en sale.order cuando se crea factura normal
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        ves = self.company_id.currency_id
        orig = self.currency_id
        invoice_vals['currency_id'] = ves.id
        new_lines = []
        for cmd in invoice_vals.get('invoice_line_ids', []):
            if isinstance(cmd, (list, tuple)) and len(cmd) == 3 and isinstance(cmd[2], dict):
                pu = cmd[2].get('price_unit', 0.0)
                invoice_vals_cmd = cmd[2]
                invoice_vals_cmd['price_unit'] = orig._convert(
                    pu, ves, self.company_id, self.date_order
                )
            new_lines.append(cmd)
        invoice_vals['invoice_line_ids'] = new_lines
        return invoice_vals

    def _create_invoices(self, grouped=False, final=False):
        moves = super()._create_invoices(grouped=grouped, final=final)
        ves = self.company_id.currency_id
        for order, move in zip(self, moves):
            if move.move_type in ('out_invoice', 'in_invoice') and move.currency_id != ves:
                orig = order.currency_id
                date = order.date_order
                for line in move.invoice_line_ids:
                    line.price_unit = orig._convert(
                        line.price_unit, ves, order.company_id, date
                    )
                move.currency_id = ves
                move._recompute_tax_lines()
                move._compute_amount()
        return moves

### 2) Convierte siempre en el wizard de anticipos
class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.model
    def _prepare_invoice_vals(self, order):
        vals = super()._prepare_invoice_vals(order)
        ves = order.company_id.currency_id
        orig = order.currency_id
        vals['currency_id'] = ves.id
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

### 3) Fallback en account.move.create para cualquier otro flujo
class AccountMove(models.Model):
    _inherit = 'account.move'

    pago_divisas = fields.Boolean(string="Pago en Divisas")
    amount_igtf = fields.Monetary(string="Impuesto igtf", compute='_compute_igtf')

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if move.move_type in ('out_invoice', 'in_invoice'):
                ves = move.company_id.currency_id
                orig = move.currency_id
                if orig and orig != ves:
                    inv_date = move.invoice_date or move.date
                    for line in move.invoice_line_ids:
                        line.price_unit = orig._convert(
                            line.price_unit, ves, move.company_id, inv_date
                        )
                    move.currency_id = ves
                    move._recompute_tax_lines()
                    move._compute_amount()
        return moves

    @api.depends('invoice_line_ids.price_subtotal','invoice_line_ids.is_igtf_line')
    def _compute_igtf(self):
        for move in self:
            move.amount_igtf = sum(
                l.price_subtotal for l in move.invoice_line_ids if l.is_igtf_line
            )

    def inserta_igtf(self):
        return True

    def action_post(self):
        for move in self:
            if move.pago_divisas and move.currency_id != move.company_id.currency_id:
                acc = (
                    move.company_id.account_igtf_id.id if move.is_sale_document()
                    else move.company_id.account_igtf_p_id.id
                )
                if not acc:
                    raise UserError(_("Configura la cuenta IGTF en la compañía."))
                prev = move.invoice_line_ids.filtered(
                    lambda l: l.is_igtf_line or l.account_id.id == acc
                )
                if prev: prev.unlink()
                base = sum(
                    l.price_subtotal for l in move.invoice_line_ids
                    if not (l.is_igtf_line or l.account_id.id == acc)
                )
                pct = move.company_id.percentage_cli_igtf or 0.0
                amt = base * pct / 100.0
                if amt:
                    move.write({'invoice_line_ids': [(0,0,{
                        'name': f"IGTF {pct:.0f}%",
                        'quantity':1,
                        'price_unit':amt,
                        'account_id':acc,
                        'is_igtf_line':True,
                    })]})
        return super().action_post()
