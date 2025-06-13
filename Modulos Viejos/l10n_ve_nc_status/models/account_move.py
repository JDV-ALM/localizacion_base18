# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    # 1) Extendemos únicamente status_in_payment (badge en la lista)
    status_in_payment = fields.Selection(
        selection_add=[('validated', 'Validado')],
    )

    # 2) Redefinimos invoice_payment_state de cero (ribbon diagonal)
    invoice_payment_state = fields.Selection(
        [
            ('not_paid',         'Sin pagar'),
            ('in_payment',       'En proceso de pago'),
            ('paid',             'Pagado'),
            ('partial',          'Pagado parcialmente'),
            ('reversed',         'Revertido'),
            ('blocked',          'Bloqueado'),
            ('invoicing_legacy', 'Sistema anterior de facturación'),
            ('draft',            'Borrador'),
            ('cancel',           'Cancelado'),
            # — nuestro nuevo estado —
            ('validated',        'Validado'),
        ],
        compute='_compute_invoice_payment_state',
        store=True,
        string='Estado de pago (Factura)',
    )

    @api.depends('payment_state', 'move_type')
    def _compute_status_in_payment(self):
        # Lógica original
        super()._compute_status_in_payment()
        # Sobreescritura puntual para NC pagadas
        for move in self:
            if move.move_type in ('out_refund', 'in_refund') and move.payment_state == 'paid':
                move.status_in_payment = 'validated'

    @api.depends('state', 'payment_state', 'move_type')
    def _compute_invoice_payment_state(self):
        # Computamos manualmente el estado de pago de la factura
        for move in self:
            # 1) NC pagada → validated
            if move.move_type in ('out_refund', 'in_refund') and move.payment_state == 'paid':
                move.invoice_payment_state = 'validated'
            # 2) Borrador / Cancelado mantienen su propio estado
            elif move.state == 'draft':
                move.invoice_payment_state = 'draft'
            elif move.state == 'cancel':
                move.invoice_payment_state = 'cancel'
            # 3) Resto: reflejamos payment_state estándar
            else:
                move.invoice_payment_state = move.payment_state or 'not_paid'
