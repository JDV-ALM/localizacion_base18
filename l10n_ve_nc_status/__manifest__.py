# -*- coding: utf-8 -*-
{
    'name': "Localización VE: Estado NC ‘Validado’",
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'author': 'Javier Gutierrez',
    'depends': ['account'],
    'assets': {
        'web.assets_backend': [
            'l10n_ve_nc_status/static/src/js/statusbar_payment.js',
        ],
    },
    'installable': True,
    'application': False,
}