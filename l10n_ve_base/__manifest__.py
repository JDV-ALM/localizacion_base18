# -*- coding: utf-8 -*-
{
    'name': 'Venezuela - Localización Base',
    'version': '18.0.1.0.0',
    'category': 'Localization/Account',
    'summary': 'Configuraciones fundamentales para localización venezolana',
    'description': """
Configuraciones fundamentales para localización venezolana

Este módulo es parte de la refactorización de la localización venezolana,
separando responsabilidades para mejor mantenibilidad.
    """,
    'author': 'Tu Nombre/Empresa',
    'website': 'https://tu-website.com',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_ve_base_views.xml',
    ],
    'installable': True,
    'application': false,
    'auto_install': true,
}
