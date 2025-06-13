# -*- coding: utf-8 -*-
{
    'name': "VE: eliminar pagos programados",
    'version': '18.0.1.0.0',
    'summary': "Quita Condición Factura y pagos programados de account.move",
    'category': 'Localization',
    'author': 'Tu Empresa / Tú',
    'depends': [
        'base_contable',
    ],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
