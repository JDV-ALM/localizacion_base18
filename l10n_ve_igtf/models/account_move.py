# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    pago_divisas = fields.Boolean(string="Pago en Divisas")

    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.is_igtf_line')
    def _compute_igtf(self):
        """
        Reemplaza el cálculo original para que 'amount_igtf' sea
        la suma de price_subtotal de las líneas marcadas como IGTF.
        """
        for move in self:
            total_igtf = sum(
                line.price_subtotal
                for line in move.invoice_line_ids
                if line.is_igtf_line
            )
            move.amount_igtf = total_igtf

    def inserta_igtf(self):
        """
        Anula cualquier inserción automática de IGTF proveniente
        de otros módulos de localización.
        """
        return True

    def action_post(self):
        """
        Al confirmar factura, si 'pago_divisas' está marcado y la
        moneda es distinta a la de la compañía:
        - Borra líneas IGTF previas
        - Calcula base imponible (líneas normales)
        - Calcula monto IGTF = base * (% configurado en company)
        - Inserta una línea con ese monto y marca is_igtf_line=True
        """
        for move in self:
            if move.pago_divisas and move.currency_id != move.company_id.currency_id:
                # Determinar cuenta IGTF según venta o compra
                account_igtf = (
                    move.company_id.account_igtf_id.id
                    if move.is_sale_document()
                    else move.company_id.account_igtf_p_id.id
                )
                if not account_igtf:
                    raise UserError(_("Configure la cuenta IGTF en la compañía."))

                # Eliminar cualquier línea IGTF previa
                to_remove = move.invoice_line_ids.filtered(
                    lambda l: l.is_igtf_line or l.account_id.id == account_igtf
                )
                if to_remove:
                    to_remove.unlink()

                # Calcular base imponible (sin líneas IGTF)
                base = sum(
                    line.price_subtotal
                    for line in move.invoice_line_ids
                    if not (line.is_igtf_line or line.account_id.id == account_igtf)
                )

                # Tomar porcentaje IGTF de la configuración de la compañía
                pct = move.company_id.percentage_cli_igtf or 0.0
                igtf_amount = base * (pct / 100.0)

                # Insertar línea IGTF si el monto es mayor a cero
                if igtf_amount:
                    move.write({
                        'invoice_line_ids': [(0, 0, {
                            'name': f"IGTF {pct:.0f}%",
                            'quantity': 1,
                            'price_unit': igtf_amount,
                            'account_id': account_igtf,
                            'is_igtf_line': True,
                        })]
                    })

        # Llamar al posteo estándar de Odoo
        return super(AccountMove, self).action_post()

    def valor_igtf_hablador(self):
        """
        Método utilizado en el QWeb del PDF para mostrar el monto de IGTF.
        """
        return self.amount_igtf
