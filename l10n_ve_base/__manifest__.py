# -*- coding: utf-8 -*-
{
    'name': "Venezuela - Base Localization",
    'version': '18.0.1.0.0',
    'summary': "Módulo base para localización contable venezolana",
    'description': """
        Módulo base para localización contable venezolana
        ================================================
        
        Este módulo proporciona las funcionalidades base para la localización 
        contable venezolana, incluyendo:
        
        * Configuraciones base para empresas venezolanas
        * Extensiones para partners (RIF, cedula)
        * Configuraciones contables específicas para Venezuela
        * Configuraciones de impuestos venezolanos
        * Configuraciones de diarios contables
        * Flujo de pagos adaptado a Venezuela
        * Reportes IGTF
        
        Colaborador: Ing. Darrell Sojo
    """,
    'category': 'Accounting/Localizations',
    'author': 'Almus',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'account_accountant',
        'account_debit_note',
        'sale',
        'purchase',
        'stock',
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_tax_views.xml',
        'views/account_journal_views.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/modo_pago_views.xml',
        'views/product_views.xml',
        'views/account_payment_register_views.xml',
        'views/purchase_views.xml',
        'views/sale_views.xml',
        'views/stock_valuation_layer_views.xml',
        'wizard/pago_wizard.xml',
        # 'wizard/report_igtf_wizard.xml',  # Comentado temporalmente
        # 'views/report_igtf_views.xml',    # Comentado temporalmente
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}