# -*- coding: utf-8 -*-


import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError




class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'


    def _prepare_default_values(self, move):
        #raise UserError(_('move tipo=%s')%move.type)
        if move.move_type in ('in_refund', 'out_refund'):
            type = 'in_invoice' if move.move_type == 'in_refund' else 'out_invoice'
        else:
            type = move.move_type
        if move.move_type=='in_invoice':
            type='in_receipt'
        if move.move_type=='out_invoice':
            type='out_receipt'
        #raise UserError(_('move tipo2=%s')%type)
        default_values = {
                'ref': '%s, %s' % (move.name, self.reason) if self.reason else move.name,
                'date': self.date or move.date,
                'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
                'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
                'invoice_payment_term_id': None,
                'debit_origin_id': move.id,
                'move_type': type,
            }
        if not self.copy_lines or move.move_type in [('in_refund', 'out_refund')]:
            default_values['line_ids'] = [(5, 0, 0)]
        return default_values
