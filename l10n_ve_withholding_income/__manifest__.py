# -*- coding: utf-8 -*-
{
    'name': 'Venezuela - Retenciones ISLR',
    'version': '18.0.1.0.0',
    'category': 'Localization/Account',
    'summary': 'Retenciones de Impuesto Sobre la Renta',
    'description': """
Retenciones de Impuesto Sobre la Renta

Este módulo es parte de la refactorización de la localización venezolana,
separando responsabilidades para mejor mantenibilidad.
    """,
    'author': 'Tu Nombre/Empresa',
    'website': 'https://tu-website.com',
    'license': 'LGPL-3',
    'depends': ['l10n_ve_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_ve_withholding_income_views.xml',
    ],
    'installable': True,
    'application': false,
    'auto_install': false,
}
