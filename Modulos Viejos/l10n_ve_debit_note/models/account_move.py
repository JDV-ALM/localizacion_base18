# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_open_debit_note(self):
        """
        Botón único: despacha a lógica de Ventas o Compras según el tipo de factura.
        """
        self.ensure_one()
        if self.move_type == 'out_invoice':
            return self._create_debit_note_sales()
        elif self.move_type == 'in_invoice':
            return self._create_debit_note_purchase()
        else:
            raise UserError(_(
                'Solo se pueden generar Notas de Débito sobre '
                'facturas de Cliente o Proveedor.'
            ))

    def _create_debit_note_sales(self):
        """
        Crea la Nota de Débito de Ventas generando manualmente líneas y impuestos.
        """
        self.ensure_one()
        # 1) Validaciones
        if self.move_type != 'out_invoice' or self.state != 'posted' or self.amount_residual <= 0:
            raise UserError(_(
                'Solo puede generar Nota de Débito desde facturas de cliente '
                'validadas con saldo pendiente.'
            ))
        # 2) Diario ND-VT
        journal = (
            self.env.ref('l10n_ve_debit_note.journal_nd_vt', raise_if_not_found=False)
            or self.env['account.journal'].search([('code', 'in', ['ND-VT', 'NDVT']), ('type', '=', 'sale')], limit=1)
        )
        if not journal:
            raise UserError(_('No se encontró el diario ND-VT para Ventas.'))
        # 3) Cálculo del diferencial cambiario
        usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not usd:
            raise UserError(_('No se encontró la moneda USD.'))
        Rate = self.env['res.currency.rate']
        inv_date = self.invoice_date or fields.Date.context_today(self)
        orig = Rate.search([('currency_id', '=', usd.id), ('name', '=', inv_date)], limit=1)
        if not orig:
            raise UserError(_('Falta la tasa para %s.') % inv_date)
        curr = Rate.search([('currency_id', '=', usd.id), ('name', '<=', fields.Date.context_today(self))],
                            order='name desc', limit=1)
        if not curr:
            raise UserError(_('Falta la tasa actual.'))
        saldo = self.amount_residual
        monto_usd      = saldo * orig.rate
        monto_bs_nuevo = monto_usd / curr.rate
        diff_amount    = monto_bs_nuevo - saldo
        if diff_amount <= 0:
            raise UserError(_(
                'No hay diferencial positivo para %s vs %s.'
            ) % (inv_date, curr.name))
        # 4) Cuenta de ingresos y impuesto
        income_acc = self.env['account.account'].search([('code', '=', '4102003')], limit=1)
        if not income_acc:
            raise UserError(_('Falta la cuenta 4102003 para diferencial de venta.'))
        iva16 = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', 16)], limit=1)
        if not iva16:
            iva16 = self.env['account.tax'].search([('name', 'ilike', 'IVA'), ('amount', '=', 16)], limit=1)
        if not iva16:
            raise UserError(_('No se encontró el impuesto de venta 16%.'))
        # 5) Construcción de las líneas
        # Línea del diferencial
        line_vals = {
            'name':       _('Diferencial cambiario'),
            'account_id': income_acc.id,
            'quantity':   1.0,
            'price_unit': diff_amount,
        }
        # Líneas de impuesto manual
        tax_amount = diff_amount * iva16.amount / 100.0
        repart = iva16.invoice_repartition_line_ids
        base_account = repart.filtered(lambda l: l.repartition_type == 'base').account_id
        tax_account  = repart.filtered(lambda l: l.repartition_type == 'tax').account_id
        base_line_vals = {
            'name':        _('Base %s') % iva16.name,
            'tax_line_id': iva16.id,
            'account_id':  base_account.id,
            'base':        diff_amount,
            'amount':      0.0,
            'sequence':    0,
        }
        tax_line_vals = {
            'name':        iva16.name,
            'tax_id':      iva16.id,
            'account_id':  tax_account.id,
            'base':        diff_amount,
            'amount':      tax_amount,
            'sequence':    1,
        }
        # 6) Abrir formulario de factura con context
        ctx = dict(self.env.context, **{
            'default_move_type':        'out_invoice',
            'default_journal_id':       journal.id,
            'default_partner_id':       self.partner_id.id,
            'default_currency_id':      self.currency_id.id,
            'default_invoice_origin':   self.name,
            'default_invoice_date':     fields.Date.context_today(self),
            'default_invoice_date_due': self.invoice_date_due or fields.Date.context_today(self),
            'default_invoice_line_ids': [(0, 0, line_vals)],
            'default_tax_line_ids':     [
                (0, 0, base_line_vals),
                (0, 0, tax_line_vals),
            ],
        })
        return {
            'name':      _('Nota de Débito Ventas'),
            'type':      'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'context':   ctx,
        }

    def _create_debit_note_purchase(self):
        """
        Crea la Nota de Débito de Compras generando manualmente líneas y
        evitando la distribución estándar que añade la línea “Base” vacía.
        """
        self.ensure_one()
        # 1) Validación
        if self.move_type != 'in_invoice' or self.state != 'posted' or self.amount_residual <= 0:
            raise UserError(_(
                'Solo puede generar Notas de Débito desde facturas de proveedor '
                'validadas con saldo pendiente.'
            ))
        # 2) Diario ND-CP
        journal = (
            self.env.ref('l10n_ve_debit_note.journal_nd_cp', raise_if_not_found=False)
            or self.env['account.journal'].search([
                ('code', 'in', ['ND-CP', 'NDPR']), ('type', '=', 'purchase')
            ], limit=1)
        )
        if not journal:
            raise UserError(_('No se encontró el diario ND-CP para Compras.'))
        # 3) Cálculo del diferencial
        usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not usd:
            raise UserError(_('No se encontró la moneda USD.'))
        Rate = self.env['res.currency.rate']
        inv_date = self.invoice_date or fields.Date.context_today(self)
        orig = Rate.search([('currency_id', '=', usd.id), ('name', '=', inv_date)], limit=1)
        if not orig:
            raise UserError(_('Falta la tasa para %s.') % inv_date)
        curr = Rate.search([('currency_id', '=', usd.id), ('name', '<=', fields.Date.context_today(self))],
                            order='name desc', limit=1)
        if not curr:
            raise UserError(_('Falta la tasa actual.'))
        saldo = self.amount_residual
        monto_usd      = saldo * orig.rate
        monto_bs_nuevo = monto_usd / curr.rate
        diff_amount    = monto_bs_nuevo - saldo
        if diff_amount <= 0:
            raise UserError(_(
                'No hay diferencial positivo para %s vs %s.'
            ) % (inv_date, curr.name))
        # 4) Cuenta de gasto e impuesto
        expense_acc = self.env['account.account'].search([('code', '=', '6008001')], limit=1)
        if not expense_acc:
            raise UserError(_('Falta la cuenta 6008001 para diferencial de compra.'))
        iva16 = self.env['account.tax'].search([('type_tax_use', '=', 'purchase'), ('amount', '=', 16)], limit=1)
        if not iva16:
            iva16 = self.env['account.tax'].search([('name', 'ilike', 'IVA'), ('amount', '=', 16)], limit=1)
        if not iva16:
            raise UserError(_('No se encontró el impuesto de compra 16%.'))
        # 5) Construcción de líneas
        line_vals = {
            'name':       _('Diferencial cambiario'),
            'account_id': expense_acc.id,
            'quantity':   1.0,
            'price_unit': diff_amount,
        }
        tax_amount = diff_amount * iva16.amount / 100.0
        repart = iva16.invoice_repartition_line_ids
        base_account = repart.filtered(lambda l: l.repartition_type == 'base').account_id
        tax_account  = repart.filtered(lambda l: l.repartition_type == 'tax').account_id
        base_line_vals = {
            'name':        _('Base %s') % iva16.name,
            'tax_line_id': iva16.id,
            'account_id':  base_account.id,
            'base':        diff_amount,
            'amount':      0.0,
            'sequence':    0,
        }
        tax_line_vals = {
            'name':        iva16.name,
            'tax_id':      iva16.id,
            'account_id':  tax_account.id,
            'base':        diff_amount,
            'amount':      tax_amount,
            'sequence':    1,
        }
        ctx = dict(self.env.context, **{
            'default_move_type':        'in_invoice',
            'default_journal_id':       journal.id,
            'default_partner_id':       self.partner_id.id,
            'default_currency_id':      self.currency_id.id,
            'default_invoice_origin':   self.name,
            'default_invoice_date':     fields.Date.context_today(self),
            'default_invoice_date_due': self.invoice_date_due or fields.Date.context_today(self),
            'default_invoice_line_ids': [(0, 0, line_vals)],
            'default_tax_line_ids':     [
                (0, 0, base_line_vals),
                (0, 0, tax_line_vals),
            ],
        })
        return {
            'name':      _('Nota de Débito Compras'),
            'type':      'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'context':   ctx,
        }
