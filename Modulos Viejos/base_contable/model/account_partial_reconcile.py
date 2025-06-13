from odoo import models, api, fields

class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    @api.depends('debit_move_id.date', 'credit_move_id.date')
    def _compute_max_date(self):
        for partial in self:
            # Recogemos sólo las fechas que existan (no False ni None)
            fechas = [
                d for d in (
                    partial.debit_move_id.date,
                    partial.credit_move_id.date
                ) if d
            ]
            # Si hay al menos una fecha, tomamos la mayor; en caso contrario, False
            partial.max_date = max(fechas) if fechas else False
