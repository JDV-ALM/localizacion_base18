# -*- coding: utf-8 -*-


from odoo import api, fields, models, _ 
from odoo.addons import decimal_precision as dp



class IslrRate(models.Model):
        _name = 'islr.rates'

        name = fields.Char(string='Rate', store=False)
        islr_concept_id = fields.Many2one('islr.concept', 'Retention  Concept', ondelete='cascade', help="Retention concept associated with this rate")
        code = fields.Char(string='Cod. Concepto', size=3, required=True, help="Concept code")
        subtotal = fields.Float(
                'No tax amount', required=True,
                help=" '%' of the amount on which to apply the retention",
                digits=dp.get_precision('Retention ISLR'))
        min = fields.Float(
                'Minimum Amount', required=True,
                digits=dp.get_precision('Retention ISLR'),
                help="Minimum amount, from which it will determine whether you"
                        " withholded")
        retention_percentage = fields.Float(
                'Cantidad %', required=True,
                digits=dp.get_precision('Retention ISLR'),
                help="The percentage to apply to taxable withold income throw the"
                        " amount to withhold")
        subtract = fields.Float(string='Subtraendos', required=True, digits=dp.get_precision('Retention ISLR'))
        residence = fields.Boolean(
                'Residence',
                help="Indicates whether a person is resident, compared with the"
                        " direction of the Company")
        natural_person =fields.Boolean(
                'Nature', help="Indicates whether a person is nature or legal")
        
        rate2 = fields.Boolean('Rate 2', help='Rate Used for Foreign Entities')
        people_type = fields.Selection(string='Tipo Persona', selection=[
        ('resident_nat_people','PNRE'),
        ('non_resit_nat_people','PNNR'),
        ('domi_ledal_entity','PJDO'),
        ('legal_ent_not_domicilied','PJND'),
        ('legal_entity_not_incorporated','PJNCD'),
        ])