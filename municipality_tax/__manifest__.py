# -*- coding: utf-8 -*-


{
        'name': 'Localización de Impuestos Municipales para Venezuela',
        'version': '18.0',
        'author': 'Grupo Angendar',
        'description': 'Impuestos Municipales',
        'category': 'Accounting/Accounting',
        'website': '',
        'images': [],
        'depends': [
            'account',
            'account_accountant',
            'base',
            'l10n_ve_dpt',
            ],
        'data': [
            'security/ir.model.access.csv',
            'data/muni.wh.concept.csv',
            'data/seq_muni_tax_data.xml',
            'data/period.month.csv',
            'data/period.year.csv',
            #'views/account_move_views.xml',
            #'views/res_partner_views.xml',
            #'views/municipality_tax_views.xml',
            #'report/report_municipal_tax.xml',
            #'views/res_company_views.xml',
            ],
        'installable': True,
        'application': True,
        'auto_install': False,
        
        }
