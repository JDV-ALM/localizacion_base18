# -*- coding: utf-8 -*-
{
    'name': "VE Factura Marca de Agua",
    'version': '18.0.1.0.0',
    'summary': "Añade marca de agua ORIGINAL/COPIA en la impresión de facturas",
    'category': 'Localization',
    'author': 'Tu Nombre o Empresa',
    'license': 'AGPL-3',
    'depends': ['account','account_reports','factura_formato_libre',],
    'data': [
         'views/report_invoice_watermark.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
