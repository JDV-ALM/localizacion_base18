{
    'name': 'Currency Rate Updater',
    'version': '1.0',
    'summary': 'Actualiza la tasa del dólar desde el BCV automáticamente.',
    'category': 'Accounting',
    'author': 'Carlos Decena',
    'version': '18.0.1.0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],
    # always loaded
    'data': [
           'data/models_data.xml',
           'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}