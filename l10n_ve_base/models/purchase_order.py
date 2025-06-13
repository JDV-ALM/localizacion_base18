# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Venezuelan purchase order fields
    supplier_invoice_number = fields.Char(
        string='Número de Factura del Proveedor',
        help='Número de factura emitido por el proveedor'
    )
    supplier_control_number = fields.Char(
        string='Número de Control del Proveedor',
        help='Número de control de la factura del proveedor'
    )
    
    # Import information
    is_import_purchase = fields.Boolean(
        string='Compra de Importación',
        help='Indica si es una compra de importación'
    )
    import_permit_number = fields.Char(
        string='Número de Permiso de Importación',
        help='Número del permiso de importación'
    )
    customs_document = fields.Char(
        string='Documento Aduanero',
        help='Número del documento aduanero'
    )
    
    # Withholding configuration
    apply_wh_vat = fields.Boolean(
        string='Aplicar Retención IVA',
        compute='_compute_withholdings',
        store=True,
        help='Aplicar retención de IVA en esta compra'
    )
    wh_vat_rate = fields.Float(
        string='Tasa Retención IVA (%)',
        default=75.0,
        help='Porcentaje de retención de IVA'
    )
    wh_vat_amount = fields.Monetary(
        string='Monto Retención IVA',
        compute='_compute_wh_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    apply_wh_islr = fields.Boolean(
        string='Aplicar Retención ISLR',
        compute='_compute_withholdings',
        store=True,
        help='Aplicar retención de ISLR en esta compra'
    )
    wh_islr_rate = fields.Float(
        string='Tasa Retención ISLR (%)',
        default=3.0,
        help='Porcentaje de retención de ISLR'
    )
    wh_islr_amount = fields.Monetary(
        string='Monto Retención ISLR',
        compute='_compute_wh_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    apply_wh_municipal = fields.Boolean(
        string='Aplicar Retención Municipal',
        compute='_compute_withholdings',
        store=True,
        help='Aplicar retención municipal en esta compra'
    )
    wh_municipal_rate = fields.Float(
        string='Tasa Retención Municipal (%)',
        default=1.0,
        help='Porcentaje de retención municipal'
    )
    wh_municipal_amount = fields.Monetary(
        string='Monto Retención Municipal',
        compute='_compute_wh_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    # Total amount after withholdings
    amount_total_with_wh = fields.Monetary(
        string='Total con Retenciones',
        compute='_compute_amount_total_with_wh',
        store=True,
        currency_field='currency_id',
        help='Total a pagar después de aplicar retenciones'
    )
    
    # Venezuelan currency fields
    currency_rate_purchase = fields.Float(
        string='Tasa de Cambio Compra',
        digits=(12, 6),
        help='Tasa de cambio utilizada en la compra'
    )
    amount_total_ves = fields.Monetary(
        string='Total en Bolívares',
        compute='_compute_amount_total_ves',
        store=True,
        help='Total de la compra en bolívares'
    )
    
    @api.depends('partner_id', 'company_id', 'amount_total')
    def _compute_withholdings(self):
        """Compute if withholdings apply"""
        for order in self:
            if order.partner_id and order.company_id:
                # Check company withholding agent status
                company = order.company_id
                
                order.apply_wh_vat = (
                    company.wh_vat_agent and 
                    order.amount_total >= 10000  # Minimum threshold
                )
                
                order.apply_wh_islr = (
                    company.wh_income_agent and
                    order.amount_total >= 3000  # Minimum threshold
                )
                
                order.apply_wh_municipal = (
                    company.wh_municipal_agent and
                    order.amount_total >= 1000  # Minimum threshold
                )
            else:
                order.apply_wh_vat = False
                order.apply_wh_islr = False
                order.apply_wh_municipal = False
    
    @api.depends('amount_untaxed', 'amount_tax', 'apply_wh_vat', 'wh_vat_rate', 
                 'apply_wh_islr', 'wh_islr_rate', 'apply_wh_municipal', 'wh_municipal_rate')
    def _compute_wh_amounts(self):
        """Compute withholding amounts"""
        for order in self:
            # IVA withholding (applied to VAT amount)
            if order.apply_wh_vat:
                order.wh_vat_amount = order.amount_tax * (order.wh_vat_rate / 100)
            else:
                order.wh_vat_amount = 0.0
            
            # ISLR withholding (applied to untaxed amount)
            if order.apply_wh_islr:
                order.wh_islr_amount = order.amount_untaxed * (order.wh_islr_rate / 100)
            else:
                order.wh_islr_amount = 0.0
            
            # Municipal withholding (applied to untaxed amount)
            if order.apply_wh_municipal:
                order.wh_municipal_amount = order.amount_untaxed * (order.wh_municipal_rate / 100)
            else:
                order.wh_municipal_amount = 0.0
    
    @api.depends('amount_total', 'wh_vat_amount', 'wh_islr_amount', 'wh_municipal_amount')
    def _compute_amount_total_with_wh(self):
        """Compute total amount after withholdings"""
        for order in self:
            total_withholdings = (
                order.wh_vat_amount + 
                order.wh_islr_amount + 
                order.wh_municipal_amount
            )
            order.amount_total_with_wh = order.amount_total - total_withholdings
    
    @api.depends('amount_total', 'currency_rate_purchase', 'currency_id')
    def _compute_amount_total_ves(self):
        """Compute total amount in Venezuelan bolívars"""
        for order in self:
            if order.currency_id.name != 'VES':
                if order.currency_rate_purchase:
                    order.amount_total_ves = order.amount_total * order.currency_rate_purchase
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
    def _onchange_currency_rate(self):
        """Update currency rate when currency or date changes"""
        if self.currency_id and self.currency_id.name != 'VES':
            ves_currency = self.env['res.currency'].search([('name', '=', 'VES')], limit=1)
            if ves_currency:
                self.currency_rate_purchase = self.currency_id._get_conversion_rate(
                    self.currency_id,
                    ves_currency,
                    self.company_id,
                    self.date_order
                )
    
    def button_confirm(self):
        """Override to add Venezuelan validations"""
        # Validate supplier invoice information
        for order in self:
            if order.is_import_purchase and not order.import_permit_number:
                raise ValidationError(_(
                    'Las compras de importación requieren número de permiso de importación'
                ))
        
        # Set currency rate if not set
        for order in self:
            if not order.currency_rate_purchase and order.currency_id.name != 'VES':
                order._onchange_currency_rate()
        
        return super().button_confirm()
    
    def _prepare_invoice(self):
        """Override to include Venezuelan invoice data"""
        invoice_vals = super()._prepare_invoice()
        
        # Add Venezuelan fields to invoice
        invoice_vals.update({
            'supplier_invoice_number': self.supplier_invoice_number,
            'supplier_control_number': self.supplier_control_number,
            'wh_vat_amount': self.wh_vat_amount,
            'wh_islr_amount': self.wh_islr_amount,
            'wh_municipal_amount': self.wh_municipal_amount,
            'currency_rate_used': self.currency_rate_purchase,
            'currency_rate_date': self.date_order,
        })
        
        return invoice_vals
    
    def get_venezuelan_purchase_info(self):
        """Get Venezuelan purchase information for reports"""
        self.ensure_one()
        return {
            'supplier_invoice': self.supplier_invoice_number or '',
            'supplier_control': self.supplier_control_number or '',
            'is_import': self.is_import_purchase,
            'import_permit': self.import_permit_number or '',
            'customs_document': self.customs_document or '',
            'withholdings': {
                'vat': self.wh_vat_amount,
                'islr': self.wh_islr_amount,
                'municipal': self.wh_municipal_amount,
                'total': self.wh_vat_amount + self.wh_islr_amount + self.wh_municipal_amount,
            },
            'total_with_wh': self.amount_total_with_wh,
            'currency_rate': self.currency_rate_purchase,
            'amount_ves': self.amount_total_ves,
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Venezuelan purchase line fields
    seniat_code = fields.Char(
        related='product_id.seniat_code',
        string='Código SENIAT',
        readonly=True
    )
    
    # Import specific fields
    import_unit_cost = fields.Float(
        string='Costo Unitario Importación',
        digits='Product Price',
        help='Costo unitario en moneda de importación'
    )
    import_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda de Importación'
    )
    
    # Tax exemption information
    tax_exempt_reason = fields.Selection(
        related='product_id.tax_exempt_reason',
        string='Motivo Exención',
        readonly=True
    )
    
    @api.onchange('product_id')
    def _onchange_product_id_venezuelan(self):
        """Set Venezuelan specific fields when product changes"""
        if self.product_id:
            # Set import currency and cost if product has foreign prices
            if self.product_id.price_usd:
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                if usd_currency:
                    self.import_currency_id = usd_currency.id
                    self.import_unit_cost = self.product_id.price_usd