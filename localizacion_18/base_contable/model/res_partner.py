# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions



class Partner(models.Model):
    _inherit = 'res.partner'

    contribuyente = fields.Selection([('no', 'No'),('si', 'Si')],default="no")
    people_type = fields.Selection(string='People type', selection=[
        ('resident_nat_people','PNRE Residente Natural Person'),
        ('non_resit_nat_people','PNNR Non-resident Natural Person'),
        ('domi_ledal_entity','PJDO Domiciled Legal Entity'),
        ('legal_ent_not_domicilied','PJDO Legal Entity Not Domiciled'),
    ], required="True")
    seniat_url = fields.Char(string='Dirección SENIAT', readonly="True", default="http://contribuyente.seniat.gob.ve/BuscaRif/BuscaRif.jsp")
    doc_tipo = fields.Selection([
        ('V','V'),
        ('E','E'),
        ('J','J'),
        ('G','G'),
        ('P','P'),
        ('C','C'),
        ])
    partner_type = fields.Selection([
        ('national','Nacional'),
        ('international','Internacional'),
    ], required=True,default='national')