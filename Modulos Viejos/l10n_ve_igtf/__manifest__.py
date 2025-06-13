# -*- coding: utf-8 -*-
{
    'name': 'Localización Venezuela - IGTF',
    'version': '18.0.1.0.0',
    'category': 'Localization/Account',
    'summary': 'Checkbox Pago en Divisas y línea automática IGTF al 3% en facturas en moneda extranjera',
    'author': 'Bluecore Networks',
    'website': 'https://bluecore-solutions.com',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'base_contable',    # módulo que ya define percentage_igtf y cuentas IGTF en res.company
    ],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
