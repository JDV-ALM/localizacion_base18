# -*- coding: utf-8 -*-
{
    'name': "l10n_ve_delivery_slip",
    'version': '18.0.1.0.0',
    'summary': "Reemplaza el título del albarán por 'GUÍA DE DESPACHO N° <número>'",
    'category': 'Warehouse',
    'author': 'Tu Nombre',
    'license': 'LGPL-3',
    'depends': ['stock'],
    'data': [
        'views/report_delivery_document_templates.xml',
    ],
    'installable': True,
    'application': False,
}
