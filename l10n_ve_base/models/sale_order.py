# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Venezuelan sale order fields
    fiscal_position_ve = fields.Selection([
        ('national', 'Venta Nacional'),
        ('export', 'Exportación'),
        ('free_zone', 'Zona Franca'),
        ('duty_free', 'Duty Free'),
    ], string='Posición Fiscal Venezolana', default='national')
    
    # Export information
    is_export_sale = fields.Boolean(
        string='Venta de Exportación',
        help='Indica si es una venta de exportación'
    )
    export_permit_number = fields.Char(
        string='Número de Permiso de Exportación',
        help='Número del permiso de exportación'
    )
    incoterm_ve = fields.Selection([
        ('EXW', 'Ex Works'),
        ('FCA', 'Free Carrier'),
        ('CPT', 'Carriage Paid To'),
        ('CIP', 'Carriage and Insurance Paid'),
        ('DAP', 'Delivered at Place'),
        ('DPU', 'Delivered at Place Unloaded'),
        ('DDP', 'Delivered Duty Paid'),
        ('FAS', 'Free Alongside Ship'),
        ('FOB', 'Free on Board'),
        ('CFR', 'Cost and Freight'),
        ('CIF', 'Cost, Insurance and Freight'),
    ], string='Incoterm')
    
    # Payment methods
    payment_method_ids = fields.Many2many(
        'modo.pago',
        string='Métodos de Pago',
        help='Métodos de pago aceptados para esta venta'
    )
    
    # IGTF configuration
    applies_igtf = fields.Boolean(
        string='Aplica IGTF',
        compute='_compute_applies_igtf',
        store=True,
        help='Indica si esta venta aplica IGTF'
    )
    igtf_amount = fields.Monetary(
        string='Monto IGTF',
        compute='_compute_igtf_amount',
        store=True,
        currency_field='currency_id',
        help='Monto del IGTF aplicable'
    )
    igtf_rate = fields.Float(
        string='Tasa IGTF (%)',
        default=3.0,
        help='Porcentaje de IGTF'
    )
    
    # Venezuelan currency fields
    currency_rate_sale = fields.Float(
        string='Tasa de Cambio Venta',
        digits=(12, 6),
        help='Tasa de cambio utilizada en la venta'
    )
    amount_total_ves = fields.Monetary(
        string='Total en Bolívares',
        compute='_compute_amount_total_ves',
        store=True,
        help='Total de la venta en bolívares'
    )
    
    # Price list in multiple currencies
    show_prices_usd = fields.Boolean(
        string='Mostrar Precios en USD',
        help='Mostrar precios en dólares estadounidenses'
    )
    show_prices_eur = fields.Boolean(
        string='Mostrar Precios en EUR',
        help='Mostrar precios en euros'
    )
    
    # Fiscal printer configuration
    use_fiscal_printer = fields.Boolean(
        string='Usar Impresora Fiscal',
        help='Esta venta utilizará impresora fiscal'
    )
    fiscal_printer_serial = fields.Char(
        string='Serial Impresora Fiscal'
    )
    
    @api.depends('payment_method_ids')
    def _compute_applies_igtf(self):
        """Compute if IGTF applies based on payment methods"""
        for order in self:
            order.applies_igtf = any(
                method.applies_igtf for method in order.payment_method_ids
            )
    
    @api.depends('amount_total', 'applies_igtf', 'igtf_rate')
    def _compute_igtf_amount(self):
        """Compute IGTF amount"""
        for order in self:
            if order.applies_igtf:
                order.igtf_amount = order.amount_total * (order.igtf_rate / 100)
            else:
                order.igtf_amount = 0.0
    
    @api.depends('amount_total', 'currency_rate_sale', 'currency_id')
    def _compute_amount_total_ves(self):
        """Compute total amount in Venezuelan bolívars"""
        for order in self:
            if order.currency_id.name != 'VES':
                if order.currency_rate_sale:
                    order.amount_total_ves = order.amount_total * order.currency_rate_sale
                else:
                    # Get current exchange rate
                    ves_currency = self.env['res.currency'].search([('name', '=', 'VES')], limit=1)
                    if ves_currency:
                        rate = order.currency_id._get_conversion_rate(
                            order.currency_id,
                            ves_currency,
                            order.company_id,
                            order.date_order
                        )
                        order.amount_total_ves = order.amount_total * rate
                    else:
                        order.amount_total_ves = order.amount_total
            else:
                order.amount_total_ves = order.amount_total
    
    @api.onchange('currency_id', 'date_order')
    def _onchange_currency_rate_sale(self):
        """Update currency rate when currency or date changes"""
        if self.currency_id and self.currency_id.name != 'VES':
            ves_currency = self.env['res.currency'].search([('name', '=', 'VES')], limit=1)
            if ves_currency:
                self.currency_rate_sale = self.currency_id._get_conversion_rate(
                    self.currency_id,
                    ves_currency,
                    self.company_id,
                    self.date_order
                )
    
    @api.onchange('fiscal_position_ve')
    def _onchange_fiscal_position_ve(self):
        """Update fields based on fiscal position"""
        if self.fiscal_position_ve == 'export':
            self.is_export_sale = True
            # Export sales typically don't have VAT
            vat_exempt_fpos = self.env['account.fiscal.position'].search([
                ('name', 'ilike', 'export'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            if vat_exempt_fpos:
                self.fiscal_position_id = vat_exempt_fpos.id
        else:
            self.is_export_sale = False
    
    def action_confirm(self):
        """Override to add Venezuelan validations"""
        # Validate export information
        for order in self:
            if order.is_export_sale and not order.export_permit_number:
                raise ValidationError(_(
                    'Las ventas de exportación requieren número de permiso de exportación'
                ))
        
        # Set currency rate if not set
        for order in self:
            if not order.currency_rate_sale and order.currency_id.name != 'VES':
                order._onchange_currency_rate_sale()
        
        return super().action_confirm()
    
    def _prepare_invoice(self):
        """Override to include Venezuelan invoice data"""
        invoice_vals = super()._prepare_invoice()
        
        # Add Venezuelan fields to invoice
        invoice_vals.update({
            'fiscal_position_ve': self.fiscal_position_ve,
            'is_export_sale': self.is_export_sale,
            'export_permit_number': self.export_permit_number,
            'payment_method_ids': [(6, 0, self.payment_method_ids.ids)],
            'applies_igtf': self.applies_igtf,
            'igtf_amount': self.igtf_amount,
            'igtf_rate': self.igtf_rate,
            'currency_rate_used': self.currency_rate_sale,
            'currency_rate_date': self.date_order,
            'use_fiscal_printer': self.use_fiscal_printer,
            'fiscal_printer_serial': self.fiscal_printer_serial,
        })
        
        return invoice_vals
    
    def get_venezuelan_sale_info(self):
        """Get Venezuelan sale information for reports"""
        self.ensure_one()
        return {
            'fiscal_position': self.fiscal_position_ve,
            'is_export': self.is_export_sale,
            'export_permit': self.export_permit_number or '',
            'incoterm': self.incoterm_ve or '',
            'payment_methods': [method.name for method in self.payment_method_ids],
            'applies_igtf': self.applies_igtf,
            'igtf_amount': self.igtf_amount,
            'currency_rate': self.currency_rate_sale,
            'amount_ves': self.amount_total_ves,
            'use_fiscal_printer': self.use_fiscal_printer,
        }
    
    def get_prices_in_currencies(self):
        """Get order prices in different currencies"""
        self.ensure_one()
        currencies_info = {
            'VES': self.amount_total_ves,
        }
        
        # Get USD price
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if usd_currency:
            if self.currency_id == usd_currency:
                currencies_info['USD'] = self.amount_total
            else:
                rate = self.currency_id._get_conversion_rate(
                    self.currency_id,
                    usd_currency,
                    self.company_id,
                    self.date_order
                )
                currencies_info['USD'] = self.amount_total * rate
        
        # Get EUR price
        eur_currency = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
        if eur_currency:
            if self.currency_id == eur_currency:
                currencies_info['EUR'] = self.amount_total
            else:
                rate = self.currency_id._get_conversion_rate(
                    self.currency_id,
                    eur_currency,
                    self.company_id,
                    self.date_order
                )
                currencies_info['EUR'] = self.amount_total * rate
        
        return currencies_info


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Venezuelan sale line fields
    seniat_code = fields.Char(
        related='product_id.seniat_code',
        string='Código SENIAT',
        readonly=True
    )
    
    # Price in multiple currencies
    price_unit_usd = fields.Float(
        string='Precio Unit. USD',
        digits='Product Price',
        compute='_compute_price_unit_usd',
        help='Precio unitario en dólares estadounidenses'
    )
    price_unit_eur = fields.Float(
        string='Precio Unit. EUR',
        digits='Product Price',
        compute='_compute_price_unit_eur',
        help='Precio unitario en euros'
    )
    
    # Tax exemption information
    tax_exempt_reason = fields.Selection(
        related='product_id.tax_exempt_reason',
        string='Motivo Exención',
        readonly=True
    )
    
    @api.depends('price_unit', 'order_id.currency_id')
    def _compute_price_unit_usd(self):
        """Compute unit price in USD"""
        for line in self:
            usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            if usd_currency and line.order_id.currency_id:
                if line.order_id.currency_id == usd_currency:
                    line.price_unit_usd = line.price_unit
                else:
                    rate = line.order_id.currency_id._get_conversion_rate(
                        line.order_id.currency_id,
                        usd_currency,
                        line.order_id.company_id,
                        line.order_id.date_order
                    )
                    line.price_unit_usd = line.price_unit * rate
            else:
                line.price_unit_usd = 0.0
    
    @api.depends('price_unit', 'order_id.currency_id')
    def _compute_price_unit_eur(self):
        """Compute unit price in EUR"""
        for line in self:
            eur_currency = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
            if eur_currency and line.order_id.currency_id:
                if line.order_id.currency_id == eur_currency:
                    line.price_unit_eur = line.price_unit
                else:
                    rate = line.order_id.currency_id._get_conversion_rate(
                        line.order_id.currency_id,
                        eur_currency,
                        line.order_id.company_id,
                        line.order_id.date_order
                    )
                    line.price_unit_eur = line.price_unit * rate
            else:
                line.price_unit_eur = 0.0