# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import re


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Venezuelan document fields
    nro_control = fields.Char(
        string='Número de Control',
        help='Número de control de la factura según normativa venezolana'
    )
    tipo_documento = fields.Selection([
        ('01', 'Factura'),
        ('02', 'Nota de Débito'),
        ('03', 'Nota de Crédito'),
        ('04', 'Factura de Exportación'),
        ('05', 'Comprobante de Retención'),
        ('06', 'Comprobante de No Retención'),
    ], string='Tipo de Documento', default='01')
    
    # Withholding fields
    wh_vat = fields.Boolean(
        string='Aplica Retención IVA',
        compute='_compute_withholdings',
        store=True
    )
    wh_vat_amount = fields.Monetary(
        string='Monto Retención IVA',
        currency_field='currency_id'
    )
    wh_vat_rate = fields.Float(
        string='Tasa Retención IVA (%)',
        default=75.0
    )
    
    wh_islr = fields.Boolean(
        string='Aplica Retención ISLR',
        compute='_compute_withholdings',
        store=True
    )
    wh_islr_amount = fields.Monetary(
        string='Monto Retención ISLR',
        currency_field='currency_id'
    )
    wh_islr_rate = fields.Float(
        string='Tasa Retención ISLR (%)',
        default=3.0
    )
    
    wh_municipal = fields.Boolean(
        string='Aplica Retención Municipal',
        compute='_compute_withholdings',
        store=True
    )
    wh_municipal_amount = fields.Monetary(
        string='Monto Retención Municipal',
        currency_field='currency_id'
    )
    wh_municipal_rate = fields.Float(
        string='Tasa Retención Municipal (%)',
        default=1.0
    )
    
    # IGTF fields
    igtf_amount = fields.Monetary(
        string='Monto IGTF',
        currency_field='currency_id',
        help='Impuesto a las Grandes Transacciones Financieras'
    )
    igtf_rate = fields.Float(
        string='Tasa IGTF (%)',
        default=3.0
    )
    applies_igtf = fields.Boolean(
        string='Aplica IGTF',
        compute='_compute_applies_igtf',
        store=True
    )
    
    # Venezuelan currency fields
    currency_rate_date = fields.Date(
        string='Fecha Tasa de Cambio',
        help='Fecha de la tasa de cambio utilizada'
    )
    currency_rate_used = fields.Float(
        string='Tasa de Cambio Utilizada',
        digits=(12, 6),
        help='Tasa de cambio utilizada en la transacción'
    )
    
    # Fiscal printing fields
    fiscal_printer = fields.Boolean(
        string='Impresora Fiscal',
        help='Documento generado por impresora fiscal'
    )
    fiscal_printer_serial = fields.Char(
        string='Serial Impresora Fiscal'
    )
    
    @api.depends('partner_id', 'move_type', 'company_id')
    def _compute_withholdings(self):
        """Compute if withholdings apply based on partner and company settings"""
        for move in self:
            if move.partner_id and move.move_type in ('out_invoice', 'in_invoice'):
                # Check if company is withholding agent
                company = move.company_id
                partner = move.partner_id
                
                # IVA withholding
                move.wh_vat = (
                    company.wh_vat_agent and 
                    move.move_type == 'out_invoice' and
                    move.amount_total >= 10000  # Minimum threshold
                )
                
                # ISLR withholding
                move.wh_islr = (
                    company.wh_income_agent and
                    move.move_type == 'out_invoice' and
                    move.amount_total >= 3000  # Minimum threshold
                )
                
                # Municipal withholding
                move.wh_municipal = (
                    company.wh_municipal_agent and
                    move.move_type == 'out_invoice' and
                    move.amount_total >= 1000  # Minimum threshold
                )
            else:
                move.wh_vat = False
                move.wh_islr = False
                move.wh_municipal = False
    
    @api.depends('journal_id', 'payment_mode')
    def _compute_applies_igtf(self):
        """Compute if IGTF applies based on payment method"""
        for move in self:
            # IGTF applies to electronic payments
            move.applies_igtf = (
                move.journal_id.type == 'bank' and
                hasattr(move, 'payment_mode') and
                move.payment_mode in ('electronic', 'transfer')
            )
    
    @api.constrains('nro_control')
    def _check_nro_control_format(self):
        """Validate control number format"""
        for move in self:
            if move.nro_control:
                # Venezuelan control number format: 8 digits
                if not re.match(r'^\d{8}$', move.nro_control):
                    raise ValidationError(_(
                        'El número de control debe tener exactamente 8 dígitos'
                    ))
    
    @api.onchange('wh_vat', 'amount_total', 'wh_vat_rate')
    def _onchange_wh_vat(self):
        """Calculate IVA withholding amount"""
        if self.wh_vat and self.amount_total:
            # Calculate VAT base (excluding VAT)
            vat_base = self.amount_untaxed
            # Apply withholding rate to VAT amount
            vat_amount = self.amount_total - self.amount_untaxed
            self.wh_vat_amount = vat_amount * (self.wh_vat_rate / 100)
    
    @api.onchange('wh_islr', 'amount_untaxed', 'wh_islr_rate')
    def _onchange_wh_islr(self):
        """Calculate ISLR withholding amount"""
        if self.wh_islr and self.amount_untaxed:
            self.wh_islr_amount = self.amount_untaxed * (self.wh_islr_rate / 100)
    
    @api.onchange('wh_municipal', 'amount_untaxed', 'wh_municipal_rate')
    def _onchange_wh_municipal(self):
        """Calculate municipal withholding amount"""
        if self.wh_municipal and self.amount_untaxed:
            self.wh_municipal_amount = self.amount_untaxed * (self.wh_municipal_rate / 100)
    
    @api.onchange('applies_igtf', 'amount_total', 'igtf_rate')
    def _onchange_igtf(self):
        """Calculate IGTF amount"""
        if self.applies_igtf and self.amount_total:
            self.igtf_amount = self.amount_total * (self.igtf_rate / 100)
    
    def _get_currency_rate(self):
        """Get current currency rate for Venezuelan bolívars"""
        self.ensure_one()
        if self.currency_id.name == 'VES':
            return 1.0
        
        # Get rate from currency rate model
        rate = self.currency_id._get_conversion_rate(
            self.currency_id,
            self.company_id.currency_id,
            self.company_id,
            self.date or fields.Date.today()
        )
        return rate
    
    def action_post(self):
        """Override to add Venezuelan validations"""
        # Validate control number uniqueness
        for move in self:
            if move.nro_control and move.move_type in ('out_invoice', 'out_refund'):
                existing = self.search([
                    ('nro_control', '=', move.nro_control),
                    ('company_id', '=', move.company_id.id),
                    ('id', '!=', move.id),
                    ('state', '=', 'posted')
                ])
                if existing:
                    raise ValidationError(_(
                        'Ya existe una factura con el número de control %s'
                    ) % move.nro_control)
        
        # Set currency rate
        for move in self:
            if not move.currency_rate_used:
                move.currency_rate_used = move._get_currency_rate()
                move.currency_rate_date = move.date
        
        return super().action_post()
    
    def get_venezuelan_taxes_summary(self):
        """Get summary of Venezuelan taxes for reports"""
        self.ensure_one()
        
        tax_summary = {
            'base_amount': self.amount_untaxed,
            'vat_amount': self.amount_total - self.amount_untaxed,
            'total_amount': self.amount_total,
            'withholdings': {
                'vat': self.wh_vat_amount if self.wh_vat else 0,
                'islr': self.wh_islr_amount if self.wh_islr else 0,
                'municipal': self.wh_municipal_amount if self.wh_municipal else 0,
            },
            'igtf': self.igtf_amount if self.applies_igtf else 0,
        }
        
        return tax_summary
    
    def _get_tax_lines_for_report(self):
        """Get tax lines formatted for Venezuelan reports"""
        tax_lines = []
        for line in self.line_ids.filtered(lambda l: l.tax_line_id):
            tax_lines.append({
                'tax_name': line.tax_line_id.name,
                'tax_amount': line.credit or line.debit,
                'tax_rate': line.tax_line_id.amount,
                'base_amount': abs(line.tax_base_amount),
            })
        return tax_lines


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Venezuelan specific fields for move lines
    wh_vat_line = fields.Boolean(
        string='Línea de Retención IVA',
        help='Indica si esta línea corresponde a retención de IVA'
    )
    wh_islr_line = fields.Boolean(
        string='Línea de Retención ISLR',
        help='Indica si esta línea corresponde a retención de ISLR'
    )
    wh_municipal_line = fields.Boolean(
        string='Línea de Retención Municipal',
        help='Indica si esta línea corresponde a retención municipal'
    )
    
    # Unit cost in foreign currency
    price_unit_foreign = fields.Float(
        string='Precio Unitario (Moneda Extranjera)',
        digits='Product Price'
    )
    foreign_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda Extranjera'
    )