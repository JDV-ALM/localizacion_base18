# -*- coding: utf-8 -*-
{
    'name': 'Venezuela - Libros Contables',
    'version': '18.0.1.0.0',
    'category': 'Localization/Account',
    'summary': 'Libro de ventas, compras y reportes contables VE',
    'description': """
Libro de ventas, compras y reportes contables VE

Este módulo es parte de la refactorización de la localización venezolana,
separando responsabilidades para mejor mantenibilidad.
    """,
    'author': 'Tu Nombre/Empresa',
    'website': 'https://tu-website.com',
    'license': 'LGPL-3',
    'depends': ['l10n_ve_base', 'l10n_ve_withholding_vat'],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_ve_accounting_reports_views.xml',
    ],
    'installable': True,
    'application': false,
    'auto_install': false,
}
