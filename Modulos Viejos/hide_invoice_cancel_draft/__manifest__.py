{
    'name': "Ocultar Anular y Reestablecer a Borrador en Facturas",
    'summary': "Esconde los botones de Anular y Reestablecer a Borrador en account.move",
    'version': '18.0.1.0.0',
    'author': "Bluecore Networks / Javier G.",
    'category': 'Accounting',
    'depends': ['account','resumen_alicuota_libros',],
    'data': [
        'views/account_move_hide_buttons.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
