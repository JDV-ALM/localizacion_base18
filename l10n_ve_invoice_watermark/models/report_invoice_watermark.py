# l10n_ve_invoice_watermark/models/report_invoice_watermark.py
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    print_count = fields.Integer(string='Veces Impresa', default=0, copy=False)

    def formato_libre(self):
        # antes de llamar al reporte, incrementamos
        for inv in self:
            inv.print_count += 1
        # llamamos al método original (el de factura_formato_libre)
        return super(AccountMove, self).formato_libre()