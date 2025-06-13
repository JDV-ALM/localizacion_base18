{
    'name': "Libro de Inventario",
    'version': '1.0',
    'summary': "Reporte Libro de Inventario en Contabilidad",
    'description': """
Módulo personalizado que permite generar el reporte Libro de Inventario.
Se accede desde: Contabilidad -> Informes -> Libro de Inventario.
El reporte presenta los datos de inventario con columnas como Código, Unidad, Descripción, Existencia Inicial, Costo Inicial, Entradas y Salidas, entre otras, siguiendo el formato del PDF de ejemplo.
""",
    'author': "Bluecore Networks",
    'depends': ['base', 'account', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/libro_inventario_wizard_view.xml',
        'views/report_libro_inventario_template.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
