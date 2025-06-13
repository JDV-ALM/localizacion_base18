# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Venezuelan identification fields
    rif = fields.Char(
        string='RIF/Cédula',
        help='Registro de Información Fiscal o Cédula de Identidad'
    )
    cedula = fields.Char(
        string='Cédula',
        help='Cédula de Identidad venezolana'
    )
    
    # Venezuelan partner type
    partner_type_ve = fields.Selection([
        ('natural', 'Persona Natural'),
        ('juridica', 'Persona Jurídica'),
        ('extranjero', 'Extranjero'),
        ('gobierno', 'Ente Gubernamental'),
    ], string='Tipo de Persona', default='natural')
    
    # Tax withholding settings
    wh_iva_agent = fields.Boolean(
        string='Agente de Retención IVA',
        default=False,
        help='Indica si es agente de retención de IVA'
    )
    wh_iva_rate = fields.Float(
        string='Tasa Retención IVA (%)',
        default=75.0,
        help='Porcentaje de retención de IVA aplicable'
    )
    
    wh_islr_agent = fields.Boolean(
        string='Agente de Retención ISLR',
        default=False,
        help='Indica si es agente de retención de ISLR'
    )
    wh_islr_rate = fields.Float(
        string='Tasa Retención ISLR (%)',
        default=3.0,
        help='Porcentaje de retención de ISLR aplicable'
    )
    
    wh_municipal_agent = fields.Boolean(
        string='Agente de Retención Municipal',
        default=False,
        help='Indica si es agente de retención municipal'
    )
    wh_municipal_rate = fields.Float(
        string='Tasa Retención Municipal (%)',
        default=1.0,
        help='Porcentaje de retención municipal aplicable'
    )
    
    # SENIAT contributor information
    seniat_updated = fields.Date(
        string='Última Actualización SENIAT',
        help='Fecha de última actualización de datos en SENIAT'
    )
    
    contribuyente_especial = fields.Boolean(
        string='Contribuyente Especial',
        default=False,
        help='Indica si es contribuyente especial según SENIAT'
    )
    
    @api.constrains('rif')
    def _check_rif_format(self):
        """Validate Venezuelan RIF/Cedula format"""
        for partner in self:
            if partner.rif:
                # Venezuelan formats:
                # RIF: J-12345678-9, V-12345678-9, E-12345678-9, etc.
                # Cedula: V-12345678, E-12345678
                if len(partner.rif) >= 9:  # Assume RIF format
                    rif_pattern = r'^[VEJPGC]-\d{7,8}-?\d?$'
                    if not re.match(rif_pattern, partner.rif.upper().replace(' ', '')):
                        raise ValidationError(_(
                            'El formato del RIF no es válido. '
                            'Debe seguir el formato: X-12345678-9 '
                            'donde X puede ser V, E, J, P, G o C'
                        ))
    
    @api.constrains('cedula')
    def _check_cedula_format(self):
        """Validate Venezuelan Cedula format"""
        for partner in self:
            if partner.cedula:
                # Venezuelan Cedula format: V-12345678 or E-12345678
                cedula_pattern = r'^[VE]-\d{6,8}$'
                if not re.match(cedula_pattern, partner.cedula.upper().replace(' ', '')):
                    raise ValidationError(_(
                        'El formato de la Cédula no es válido. '
                        'Debe seguir el formato: V-12345678 o E-12345678'
                    ))
    
    @api.onchange('partner_type_ve')
    def _onchange_partner_type_ve(self):
        """Set default values based on partner type"""
        if self.partner_type_ve == 'juridica':
            self.is_company = True
        elif self.partner_type_ve == 'natural':
            self.is_company = False
    
    @api.onchange('rif', 'cedula')
    def _onchange_identification(self):
        """Sync RIF and Cedula fields"""
        if self.rif and not self.cedula:
            # If RIF looks like a cedula (V- or E- prefix), copy to cedula
            if self.rif.upper().startswith(('V-', 'E-')) and len(self.rif) <= 11:
                self.cedula = self.rif
        elif self.cedula and not self.rif:
            self.rif = self.cedula
    
    def name_get(self):
        """Override name_get to include RIF/Cedula in display"""
        result = []
        for partner in self:
            name = partner.name or ''
            if partner.rif:
                name = f"{name} ({partner.rif})"
            result.append((partner.id, name))
        return result
    
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=100, order=None):
        """Override name search to include RIF/Cedula search"""
        if name:
            domain = domain or []
            # Search by RIF/Cedula if the search term looks like one
            if re.match(r'^[VEJPGC]-?\d', name.upper()):
                domain = ['|', '|', 
                         ('rif', operator, name),
                         ('cedula', operator, name),
                         ('name', operator, name)] + domain
            else:
                domain = ['|', '|', 
                         ('name', operator, name),
                         ('rif', operator, name),
                         ('cedula', operator, name)] + domain
        
        return self._search(domain, limit=limit, order=order)
    
    def get_partner_fiscal_info(self):
        """Get partner fiscal information for Venezuelan documents"""
        self.ensure_one()
        return {
            'name': self.name,
            'rif': self.rif or self.cedula or '',
            'address': self._get_partner_address(),
            'phone': self.phone or '',
            'email': self.email or '',
            'partner_type': self.partner_type_ve,
            'is_wh_agent': any([
                self.wh_iva_agent,
                self.wh_islr_agent, 
                self.wh_municipal_agent
            ]),
        }
    
    def _get_partner_address(self):
        """Get formatted partner address"""
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