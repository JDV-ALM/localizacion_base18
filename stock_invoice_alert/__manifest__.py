# -*- coding: utf-8 #
{
    'name': 'Stock Invoice Alert Banner',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'summary': 'Muestra una barra con el número de guías de despacho sin facturar',
    'category': 'Tools',
    'author': 'Bluecore Solutions',
    'depends': [
        'stock',
        'web',
    ],
    'data': [
        'views/alert_views.xml',
    ],
    'installable': True,
    'application': True,
}