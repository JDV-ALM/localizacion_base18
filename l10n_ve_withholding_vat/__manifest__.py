# -*- coding: utf-8 -*-
{
    'name': 'Venezuela - Retenciones IVA',
    'version': '18.0.1.0.0',
    'category': 'Localization/Account',
    'summary': 'Comprobantes de retención de IVA',
    'description': """
Comprobantes de retención de IVA

Este módulo es parte de la refactorización de la localización venezolana,
separando responsabilidades para mejor mantenibilidad.
    """,
    'author': 'Tu Nombre/Empresa',
    'website': 'https://tu-website.com',
    'license': 'LGPL-3',
    'depends': ['l10n_ve_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_ve_withholding_vat_views.xml',
    ],
    'installable': True,
    'application': false,
    'auto_install': false,
}
