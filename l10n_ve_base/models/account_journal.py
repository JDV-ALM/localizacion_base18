# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    # Venezuelan journal configurations
    journal_type_ve = fields.Selection([
        ('sale', 'Ventas'),
        ('purchase', 'Compras'),
        ('cash', 'Efectivo'),
        ('bank', 'Banco'),
        ('general', 'Operaciones Diversas'),
        ('opening', 'Situación Inicial'),
        ('closing', 'Cierre'),
        ('adjustment', 'Ajustes'),
        ('withholding', 'Retenciones'),
    ], string='Tipo Diario Venezolano')
    
    # Fiscal printer configuration
    fiscal_printer = fields.Boolean(
        string='Impresora Fiscal',
        help='Este diario usa impresora fiscal'
    )
    fiscal_printer_serial = fields.Char(
        string='Serial Impresora Fiscal'
    )
    
    # Document numbering for Venezuelan compliance
    invoice_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia de Facturas',
        help='Secuencia para numeración de facturas'
    )
    control_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia Número de Control',
        help='Secuencia para números de control'
    )
    
    # Bank specific fields for Venezuela
    bank_account_type_ve = fields.Selection([
        ('corriente', 'Cuenta Corriente'),
        ('ahorro', 'Cuenta de Ahorro'),
        ('plazo_fijo', 'Plazo Fijo'),
        ('credito', 'Línea de Crédito'),
    ], string='Tipo de Cuenta Bancaria')
    
    bank_code = fields.Char(
        string='Código del Banco',
        help='Código de 4 dígitos del banco venezolano'
    )
    
    # IGTF configuration
    applies_igtf = fields.Boolean(
        string='Aplica IGTF',
        help='Este diario aplica IGTF para transacciones electrónicas'
    )
    igtf_tax_id = fields.Many2one(
        'account.tax',
        string='Impuesto IGTF',
        domain=[('is_igtf', '=', True)]
    )
    
    # Withholding journals
    is_withholding_journal = fields.Boolean(
        string='Diario de Retenciones',
        help='Este diario es específico para retenciones'
    )
    withholding_type = fields.Selection([
        ('wh_vat', 'Retención IVA'),
        ('wh_islr', 'Retención ISLR'),
        ('wh_municipal', 'Retención Municipal'),
    ], string='Tipo de Retención')
    
    # Currency exchange journal
    is_currency_exchange = fields.Boolean(
        string='Diario de Diferencial Cambiario',
        help='Este diario maneja diferencias cambiarias'
    )
    
    @api.constrains('bank_code')
    def _check_bank_code_format(self):
        """Validate Venezuelan bank code format"""
        for journal in self:
            if journal.bank_code:
                if not journal.bank_code.isdigit() or len(journal.bank_code) != 4:
                    raise ValidationError(_(
                        'El código del banco debe tener exactamente 4 dígitos'
                    ))
    
    @api.onchange('type')
    def _onchange_type(self):
        """Set Venezuelan journal type based on standard type"""
        super()._onchange_type()
        if self.type == 'sale':
            self.journal_type_ve = 'sale'
        elif self.type == 'purchase':
            self.journal_type_ve = 'purchase'
        elif self.type == 'cash':
            self.journal_type_ve = 'cash'
        elif self.type == 'bank':
            self.journal_type_ve = 'bank'
            self.applies_igtf = True
        elif self.type == 'general':
            self.journal_type_ve = 'general'
    
    @api.onchange('applies_igtf')
    def _onchange_applies_igtf(self):
        """Set IGTF tax when IGTF is enabled"""
        if self.applies_igtf and not self.igtf_tax_id:
            igtf_tax = self.env['account.tax'].search([
                ('is_igtf', '=', True),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            if igtf_tax:
                self.igtf_tax_id = igtf_tax.id
    
    @api.onchange('is_withholding_journal')
    def _onchange_is_withholding_journal(self):
        """Configure withholding journal settings"""
        if self.is_withholding_journal:
            self.type = 'general'
            self.journal_type_ve = 'withholding'
    
    @api.model
    def create(self, vals):
        """Override create to set up Venezuelan sequences"""
        journal = super().create(vals)
        
        # Create control number sequence for sales journals
        if journal.type == 'sale' and not journal.control_sequence_id:
            sequence_vals = {
                'name': f'Control {journal.name}',
                'code': f'account.move.control.{journal.id}',
                'prefix': '',
                'suffix': '',
                'padding': 8,
                'number_next': 1,
                'number_increment': 1,
                'company_id': journal.company_id.id,
            }
            control_sequence = self.env['ir.sequence'].create(sequence_vals)
            journal.control_sequence_id = control_sequence.id
        
        return journal
    
    def get_next_control_number(self):
        """Get next control number for invoices"""
        self.ensure_one()
        if self.control_sequence_id:
            return self.control_sequence_id.next_by_id()
        return False
    
    def get_venezuelan_bank_info(self):
        """Get Venezuelan bank information"""
        self.ensure_one()
        if self.type == 'bank':
            return {
                'bank_name': self.bank_id.name if self.bank_id else '',
                'bank_code': self.bank_code or '',
                'account_number': self.bank_acc_number or '',
                'account_type': self.bank_account_type_ve or '',
                'applies_igtf': self.applies_igtf,
            }
        return {}
    
    @api.model
    def create_venezuelan_default_journals(self, company):
        """Create default Venezuelan journals for a company"""
        journals_data = [
            {
                'name': 'Facturas de Ventas',
                'code': 'FAV',
                'type': 'sale',
                'journal_type_ve': 'sale',
                'fiscal_printer': True,
                'company_id': company.id,
            },
            {
                'name': 'Facturas de Compras',
                'code': 'FAC',
                'type': 'purchase',
                'journal_type_ve': 'purchase',
                'company_id': company.id,
            },
            {
                'name': 'Retenciones IVA',
                'code': 'RIVA',
                'type': 'general',
                'journal_type_ve': 'withholding',
                'is_withholding_journal': True,
                'withholding_type': 'wh_vat',
                'company_id': company.id,
            },
            {
                'name': 'Retenciones ISLR',
                'code': 'RISL',
                'type': 'general',
                'journal_type_ve': 'withholding',
                'is_withholding_journal': True,
                'withholding_type': 'wh_islr',
                'company_id': company.id,
            },
            {
                'name': 'Retenciones Municipales',
                'code': 'RMUN',
                'type': 'general',
                'journal_type_ve': 'withholding',
                'is_withholding_journal': True,
                'withholding_type': 'wh_municipal',
                'company_id': company.id,
            },
            {
                'name': 'Diferencial Cambiario',
                'code': 'DICAM',
                'type': 'general',
                'journal_type_ve': 'adjustment',
                'is_currency_exchange': True,
                'company_id': company.id,
            },
            {
                'name': 'Efectivo',
                'code': 'EFEC',
                'type': 'cash',
                'journal_type_ve': 'cash',
                'company_id': company.id,
            },
        ]
        
        created_journals = []
        for journal_data in journals_data:
            existing_journal = self.search([
                ('code', '=', journal_data['code']),
                ('company_id', '=', company.id)
            ], limit=1)
            if not existing_journal:
                journal = self.create(journal_data)
                created_journals.append(journal)
        
        return created_journals