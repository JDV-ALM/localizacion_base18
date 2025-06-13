# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Venezuelan company identification fields
    rif = fields.Char(
        string='RIF',
        help='Registro de Información Fiscal (RIF) de la empresa venezolana'
    )
    nit = fields.Char(
        string='NIT',
        help='Número de Identificación Tributaria'
    )
    
    # Venezuelan accounting configurations
    wh_agent = fields.Boolean(
        string='Agente de Retención',
        default=False,
        help='Indica si la empresa es agente de retención de impuestos'
    )
    wh_vat_agent = fields.Boolean(
        string='Agente de Retención IVA',
        default=False,
        help='Indica si la empresa es agente de retención de IVA'
    )
    wh_income_agent = fields.Boolean(
        string='Agente de Retención ISLR',
        default=False,
        help='Indica si la empresa es agente de retención de ISLR'
    )
    wh_municipal_agent = fields.Boolean(
        string='Agente de Retención Municipal',
        default=False,
        help='Indica si la empresa es agente de retención municipal'
    )
    
    # IGTF Configuration
    igtf_tax_id = fields.Many2one(
        'account.tax',
        string='Impuesto IGTF',
        help='Impuesto a las Grandes Transacciones Financieras'
    )
    
    # Venezuelan localization settings
    seniat_url = fields.Char(
        string='URL SENIAT',
        default='http://www.seniat.gob.ve/',
        help='URL del portal del SENIAT'
    )
    
    @api.constrains('rif')
    def _check_rif_format(self):
        """Validate Venezuelan RIF format"""
        for company in self:
            if company.rif:
                # Venezuelan RIF format: J-12345678-9 or V-12345678-9, etc.
                rif_pattern = r'^[VEJPG]-\d{8}-\d$'
                if not re.match(rif_pattern, company.rif.upper().replace(' ', '')):
                    raise ValidationError(_(
                        'El formato del RIF no es válido. '
                        'Debe seguir el formato: X-12345678-9 '
                        'donde X puede ser V, E, J, P o G'
                    ))
    
    @api.model
    def create(self, vals):
        """Override create to set Venezuelan defaults"""
        company = super(ResCompany, self).create(vals)
        
        # Set Venezuelan country if not specified
        if not company.country_id:
            venezuela = self.env['res.country'].search([('code', '=', 'VE')], limit=1)
            if venezuela:
                company.country_id = venezuela.id
        
        return company
    
    def get_fiscal_printer_info(self):
        """Get fiscal printer information for Venezuelan compliance"""
        self.ensure_one()
        return {
            'company_name': self.name,
            'rif': self.rif or '',
            'address': self._get_company_address(),
            'phone': self.phone or '',
        }
    
    def _get_company_address(self):
        """Get formatted company address"""
        self.ensure_one()
        address_parts = []
        if self.street:
            address_parts.append(self.street)
        if self.street2:
            address_parts.append(self.street2)
        if self.city:
            address_parts.append(self.city)
        if self.state_id:
            address_parts.append(self.state_id.name)
        if self.zip:
            address_parts.append(self.zip)
        return ', '.join(address_parts)