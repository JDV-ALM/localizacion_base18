# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import io
try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class ReportIGTFWizard(models.TransientModel):
    _name = 'report.igtf.wizard'
    _description = 'Asistente de Reporte IGTF'

    # Report parameters
    date_from = fields.Date(
        string='Fecha Desde',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
        help='Fecha inicial del reporte'
    )
    
    date_to = fields.Date(
        string='Fecha Hasta',
        required=True,
        default=fields.Date.today,
        help='Fecha final del reporte'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía para generar el reporte'
    )
    
    # Report type
    report_type = fields.Selection([
        ('summary', 'Resumen IGTF'),
        ('detailed', 'Detallado por Transacción'),
        ('by_partner', 'Por Cliente/Proveedor'),
        ('by_payment_method', 'Por Método de Pago'),
    ], string='Tipo de Reporte', required=True, default='summary')
    
    # Filters
    partner_ids = fields.Many2many(
        'res.partner',
        string='Clientes/Proveedores',
        help='Filtrar por clientes/proveedores específicos'
    )
    
    journal_ids = fields.Many2many(
        'account.journal',
        string='Diarios',
        domain=[('type', 'in', ['bank', 'cash'])],
        help='Filtrar por diarios específicos'
    )
    
    payment_method_ids = fields.Many2many(
        'modo.pago',
        string='Métodos de Pago',
        domain=[('applies_igtf', '=', True)],
        help='Filtrar por métodos de pago que aplican IGTF'
    )
    
    # Export options
    export_format = fields.Selection([
        ('screen', 'Mostrar en Pantalla'),
        ('pdf', 'Exportar PDF'),
        ('excel', 'Exportar Excel'),
    ], string='Formato de Exportación', required=True, default='screen')
    
    # Results
    report_data = fields.Text(
        string='Datos del Reporte',
        readonly=True
    )
    
    report_file = fields.Binary(
        string='Archivo del Reporte',
        readonly=True
    )
    
    report_filename = fields.Char(
        string='Nombre del Archivo',
        readonly=True
    )
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Validate date range"""
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise UserError(_('La fecha inicial no puede ser mayor a la fecha final'))
    
    def action_generate_report(self):
        """Generate IGTF report"""
        self.ensure_one()
        
        # Get report data
        report_data = self._get_igtf_data()
        
        if self.export_format == 'screen':
            return self._show_report_screen(report_data)
        elif self.export_format == 'pdf':
            return self._export_pdf(report_data)
        elif self.export_format == 'excel':
            return self._export_excel(report_data)
    
    def _get_igtf_data(self):
        """Get IGTF data based on report type"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
            ('applies_igtf', '=', True),
            ('igtf_amount', '>', 0),
            ('state', '=', 'posted'),
        ]
        
        # Apply filters
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        
        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))
        
        if self.payment_method_ids:
            domain.append(('payment_method_ve', 'in', self.payment_method_ids.ids))
        
        # Get payments with IGTF
        payments = self.env['account.payment'].search(domain)
        
        # Also get invoices with IGTF
        invoice_domain = [
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
            ('applies_igtf', '=', True),
            ('igtf_amount', '>', 0),
            ('state', '=', 'posted'),
        ]
        
        if self.partner_ids:
            invoice_domain.append(('partner_id', 'in', self.partner_ids.ids))
        
        invoices = self.env['account.move'].search(invoice_domain)
        
        # Process data based on report type
        if self.report_type == 'summary':
            return self._process_summary_data(payments, invoices)
        elif self.report_type == 'detailed':
            return self._process_detailed_data(payments, invoices)
        elif self.report_type == 'by_partner':
            return self._process_by_partner_data(payments, invoices)
        elif self.report_type == 'by_payment_method':
            return self._process_by_payment_method_data(payments, invoices)
    
    def _process_summary_data(self, payments, invoices):
        """Process summary IGTF data"""
        total_payments = sum(payments.mapped('amount'))
        total_igtf_payments = sum(payments.mapped('igtf_amount'))
        
        total_invoices = sum(invoices.mapped('amount_total'))
        total_igtf_invoices = sum(invoices.mapped('igtf_amount'))
        
        return {
            'type': 'summary',
            'period': f"{self.date_from.strftime('%d/%m/%Y')} - {self.date_to.strftime('%d/%m/%Y')}",
            'company': self.company_id.name,
            'payments': {
                'count': len(payments),
                'total_amount': total_payments,
                'total_igtf': total_igtf_payments,
            },
            'invoices': {
                'count': len(invoices),
                'total_amount': total_invoices,
                'total_igtf': total_igtf_invoices,
            },
            'totals': {
                'total_base': total_payments + total_invoices,
                'total_igtf': total_igtf_payments + total_igtf_invoices,
                'total_with_igtf': total_payments + total_invoices + total_igtf_payments + total_igtf_invoices,
            }
        }
    
    def _process_detailed_data(self, payments, invoices):
        """Process detailed IGTF data"""
        transactions = []
        
        # Process payments
        for payment in payments:
            transactions.append({
                'date': payment.date,
                'type': 'Pago',
                'document': payment.name,
                'partner': payment.partner_id.name,
                'payment_method': payment.payment_method_ve.name if payment.payment_method_ve else '',
                'base_amount': payment.amount - payment.igtf_amount,
                'igtf_rate': payment.igtf_rate,
                'igtf_amount': payment.igtf_amount,
                'total_amount': payment.amount,
            })
        
        # Process invoices
        for invoice in invoices:
            transactions.append({
                'date': invoice.invoice_date,
                'type': 'Factura',
                'document': invoice.name,
                'partner': invoice.partner_id.name,
                'payment_method': ', '.join(invoice.payment_method_ids.mapped('name')),
                'base_amount': invoice.amount_total - invoice.igtf_amount,
                'igtf_rate': invoice.igtf_rate,
                'igtf_amount': invoice.igtf_amount,
                'total_amount': invoice.amount_total,
            })
        
        # Sort by date
        transactions.sort(key=lambda x: x['date'])
        
        return {
            'type': 'detailed',
            'period': f"{self.date_from.strftime('%d/%m/%Y')} - {self.date_to.strftime('%d/%m/%Y')}",
            'company': self.company_id.name,
            'transactions': transactions,
            'totals': {
                'count': len(transactions),
                'total_base': sum(t['base_amount'] for t in transactions),
                'total_igtf': sum(t['igtf_amount'] for t in transactions),
                'total_with_igtf': sum(t['total_amount'] for t in transactions),
            }
        }
    
    def _process_by_partner_data(self, payments, invoices):
        """Process IGTF data by partner"""
        partner_data = {}
        
        # Process payments
        for payment in payments:
            partner_id = payment.partner_id.id
            if partner_id not in partner_data:
                partner_data[partner_id] = {
                    'name': payment.partner_id.name,
                    'rif': payment.partner_id.rif or '',
                    'payments_count': 0,
                    'invoices_count': 0,
                    'total_base': 0,
                    'total_igtf': 0,
                    'total_amount': 0,
                }
            
            partner_data[partner_id]['payments_count'] += 1
            partner_data[partner_id]['total_base'] += payment.amount - payment.igtf_amount
            partner_data[partner_id]['total_igtf'] += payment.igtf_amount
            partner_data[partner_id]['total_amount'] += payment.amount
        
        # Process invoices
        for invoice in invoices:
            partner_id = invoice.partner_id.id
            if partner_id not in partner_data:
                partner_data[partner_id] = {
                    'name': invoice.partner_id.name,
                    'rif': invoice.partner_id.rif or '',
                    'payments_count': 0,
                    'invoices_count': 0,
                    'total_base': 0,
                    'total_igtf': 0,
                    'total_amount': 0,
                }
            
            partner_data[partner_id]['invoices_count'] += 1
            partner_data[partner_id]['total_base'] += invoice.amount_total - invoice.igtf_amount
            partner_data[partner_id]['total_igtf'] += invoice.igtf_amount
            partner_data[partner_id]['total_amount'] += invoice.amount_total
        
        partners = list(partner_data.values())
        partners.sort(key=lambda x: x['name'])
        
        return {
            'type': 'by_partner',
            'period': f"{self.date_from.strftime('%d/%m/%Y')} - {self.date_to.strftime('%d/%m/%Y')}",
            'company': self.company_id.name,
            'partners': partners,
            'totals': {
                'partners_count': len(partners),
                'total_base': sum(p['total_base'] for p in partners),
                'total_igtf': sum(p['total_igtf'] for p in partners),
                'total_amount': sum(p['total_amount'] for p in partners),
            }
        }
    
    def _process_by_payment_method_data(self, payments, invoices):
        """Process IGTF data by payment method"""
        method_data = {}
        
        # Process payments
        for payment in payments:
            method_key = payment.payment_method_ve.name if payment.payment_method_ve else 'Sin Método'
            if method_key not in method_data:
                method_data[method_key] = {
                    'name': method_key,
                    'count': 0,
                    'total_base': 0,
                    'total_igtf': 0,
                    'total_amount': 0,
                }
            
            method_data[method_key]['count'] += 1
            method_data[method_key]['total_base'] += payment.amount - payment.igtf_amount
            method_data[method_key]['total_igtf'] += payment.igtf_amount
            method_data[method_key]['total_amount'] += payment.amount
        
        # Process invoices
        for invoice in invoices:
            methods = invoice.payment_method_ids.mapped('name')
            method_key = ', '.join(methods) if methods else 'Sin Método'
            if method_key not in method_data:
                method_data[method_key] = {
                    'name': method_key,
                    'count': 0,
                    'total_base': 0,
                    'total_igtf': 0,
                    'total_amount': 0,
                }
            
            method_data[method_key]['count'] += 1
            method_data[method_key]['total_base'] += invoice.amount_total - invoice.igtf_amount
            method_data[method_key]['total_igtf'] += invoice.igtf_amount
            method_data[method_key]['total_amount'] += invoice.amount_total
        
        methods = list(method_data.values())
        methods.sort(key=lambda x: x['name'])
        
        return {
            'type': 'by_payment_method',
            'period': f"{self.date_from.strftime('%d/%m/%Y')} - {self.date_to.strftime('%d/%m/%Y')}",
            'company': self.company_id.name,
            'methods': methods,
            'totals': {
                'methods_count': len(methods),
                'total_base': sum(m['total_base'] for m in methods),
                'total_igtf': sum(m['total_igtf'] for m in methods),
                'total_amount': sum(m['total_amount'] for m in methods),
            }
        }
    
    def _show_report_screen(self, report_data):
        """Show report on screen"""
        self.report_data = str(report_data)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reporte IGTF'),
            'res_model': 'report.igtf.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'show_report': True},
        }
    
    def _export_excel(self, report_data):
        """Export report to Excel"""
        if not xlsxwriter:
            raise UserError(_('La librería xlsxwriter no está instalada'))
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Create worksheet
        worksheet = workbook.add_worksheet('Reporte IGTF')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        subheader_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#D9D9D9'
        })
        
        currency_format = workbook.add_format({
            'num_format': '#,##0.00'
        })
        
        # Write header
        worksheet.merge_range('A1:F1', f'REPORTE IGTF - {report_data["company"]}', header_format)
        worksheet.merge_range('A2:F2', f'Período: {report_data["period"]}', header_format)
        
        row = 4
        
        if report_data['type'] == 'summary':
            self._write_summary_excel(worksheet, report_data, row, subheader_format, currency_format)
        elif report_data['type'] == 'detailed':
            self._write_detailed_excel(worksheet, report_data, row, subheader_format, currency_format)
        elif report_data['type'] == 'by_partner':
            self._write_by_partner_excel(worksheet, report_data, row, subheader_format, currency_format)
        elif report_data['type'] == 'by_payment_method':
            self._write_by_method_excel(worksheet, report_data, row, subheader_format, currency_format)
        
        workbook.close()
        output.seek(0)
        
        # Save file
        filename = f"reporte_igtf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        self.report_file = base64.b64encode(output.read())
        self.report_filename = filename
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=report.igtf.wizard&id={self.id}&field=report_file&download=true&filename={filename}',
            'target': 'self',
        }
    
    def _write_summary_excel(self, worksheet, data, start_row, subheader_format, currency_format):
        """Write summary data to Excel"""
        worksheet.write(start_row, 0, 'RESUMEN', subheader_format)
        
        row = start_row + 2
        worksheet.write(row, 0, 'Pagos:')
        worksheet.write(row, 1, data['payments']['count'])
        worksheet.write(row, 2, data['payments']['total_amount'], currency_format)
        worksheet.write(row, 3, data['payments']['total_igtf'], currency_format)
        
        row += 1
        worksheet.write(row, 0, 'Facturas:')
        worksheet.write(row, 1, data['invoices']['count'])
        worksheet.write(row, 2, data['invoices']['total_amount'], currency_format)
        worksheet.write(row, 3, data['invoices']['total_igtf'], currency_format)
        
        row += 2
        worksheet.write(row, 0, 'TOTALES:', subheader_format)
        worksheet.write(row, 1, 'Base:', subheader_format)
        worksheet.write(row, 2, data['totals']['total_base'], currency_format)
        
        row += 1
        worksheet.write(row, 1, 'IGTF:', subheader_format)
        worksheet.write(row, 2, data['totals']['total_igtf'], currency_format)
        
        row += 1
        worksheet.write(row, 1, 'Total con IGTF:', subheader_format)
        worksheet.write(row, 2, data['totals']['total_with_igtf'], currency_format)
    
    def _write_detailed_excel(self, worksheet, data, start_row, subheader_format, currency_format):
        """Write detailed data to Excel"""
        # Headers
        headers = ['Fecha', 'Tipo', 'Documento', 'Cliente/Proveedor', 'Método Pago', 'Base', 'IGTF', 'Total']
        for col, header in enumerate(headers):
            worksheet.write(start_row, col, header, subheader_format)
        
        # Data
        row = start_row + 1
        for transaction in data['transactions']:
            worksheet.write(row, 0, transaction['date'].strftime('%d/%m/%Y'))
            worksheet.write(row, 1, transaction['type'])
            worksheet.write(row, 2, transaction['document'])
            worksheet.write(row, 3, transaction['partner'])
            worksheet.write(row, 4, transaction['payment_method'])
            worksheet.write(row, 5, transaction['base_amount'], currency_format)
            worksheet.write(row, 6, transaction['igtf_amount'], currency_format)
            worksheet.write(row, 7, transaction['total_amount'], currency_format)
            row += 1
        
        # Totals
        row += 1
        worksheet.write(row, 4, 'TOTALES:', subheader_format)
        worksheet.write(row, 5, data['totals']['total_base'], currency_format)
        worksheet.write(row, 6, data['totals']['total_igtf'], currency_format)
        worksheet.write(row, 7, data['totals']['total_with_igtf'], currency_format)
    
    def _write_by_partner_excel(self, worksheet, data, start_row, subheader_format, currency_format):
        """Write by partner data to Excel"""
        # Headers
        headers = ['Cliente/Proveedor', 'RIF', 'Pagos', 'Facturas', 'Base', 'IGTF', 'Total']
        for col, header in enumerate(headers):
            worksheet.write(start_row, col, header, subheader_format)
        
        # Data
        row = start_row + 1
        for partner in data['partners']:
            worksheet.write(row, 0, partner['name'])
            worksheet.write(row, 1, partner['rif'])
            worksheet.write(row, 2, partner['payments_count'])
            worksheet.write(row, 3, partner['invoices_count'])
            worksheet.write(row, 4, partner['total_base'], currency_format)
            worksheet.write(row, 5, partner['total_igtf'], currency_format)
            worksheet.write(row, 6, partner['total_amount'], currency_format)
            row += 1
        
        # Totals
        row += 1
        worksheet.write(row, 3, 'TOTALES:', subheader_format)
        worksheet.write(row, 4, data['totals']['total_base'], currency_format)
        worksheet.write(row, 5, data['totals']['total_igtf'], currency_format)
        worksheet.write(row, 6, data['totals']['total_amount'], currency_format)
    
    def _write_by_method_excel(self, worksheet, data, start_row, subheader_format, currency_format):
        """Write by payment method data to Excel"""
        # Headers
        headers = ['Método de Pago', 'Transacciones', 'Base', 'IGTF', 'Total']
        for col, header in enumerate(headers):
            worksheet.write(start_row, col, header, subheader_format)
        
        # Data
        row = start_row + 1
        for method in data['methods']:
            worksheet.write(row, 0, method['name'])
            worksheet.write(row, 1, method['count'])
            worksheet.write(row, 2, method['total_base'], currency_format)
            worksheet.write(row, 3, method['total_igtf'], currency_format)
            worksheet.write(row, 4, method['total_amount'], currency_format)
            row += 1
        
        # Totals
        row += 1
        worksheet.write(row, 1, 'TOTALES:', subheader_format)
        worksheet.write(row, 2, data['totals']['total_base'], currency_format)
        worksheet.write(row, 3, data['totals']['total_igtf'], currency_format)
        worksheet.write(row, 4, data['totals']['total_amount'], currency_format)