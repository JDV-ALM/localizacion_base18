# -*- coding: utf-8 -*-
{
    'name': "Ocultar Ruta TXT IVA",
    'version': "1.0",
    'author': "Tu Empresa",
    'category': "Localization",
    'summary': "Oculta el campo ‘Ruta archivo txt I.V.A.’ de la ficha de la compañía",
    'depends': ["base", "base_contable", "txt_iva"],
    'data': [
        "views/res_company_hide_txt_iva.xml",
    ],
    'installable': True,
    'application': False,
}
