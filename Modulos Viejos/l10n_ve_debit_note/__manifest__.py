# -*- coding: utf-8 -*-
{
    'name': 'l10n_ve Debit Note',
    'version': '18.0.1.0.0',
    'category': 'Localization',
    'summary': 'Notas de Débito y diferencial cambiario',
    'depends': [
        'base_contable',
        'account',
        'l10n_ve_invoice_flow',
        'sale',
        'purchase',
    ],
    'data': [
        "data/debit_note_data.xml",
        "data/journal_nd_cp.xml",
        "views/account_move_views.xml",
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
