from odoo import models, fields

class LibroInventarioWizardLine(models.TransientModel):
    _name = 'libro.inventario.wizard.line'
    _description = 'Línea del Wizard para Libro de Inventario'

    wizard_id = fields.Many2one('libro.inventario.wizard', string="Wizard")
    code = fields.Char("Código")
    unit = fields.Char("Unidad")
    description = fields.Char("Descripción")

    initial_qty       = fields.Float("Existencia Inicial", digits=(12,2))
    initial_cost      = fields.Float("Costo Unit. Inicial", digits=(12,2))
    initial_total     = fields.Float("Total Bs. Inicial", digits=(12,2))

    entries           = fields.Float("Entradas (Cant.)", digits=(12,2))
    entries_cost_unit = fields.Float("Costo Unit. Entradas", digits=(12,2))
    entries_total     = fields.Float("Total Bs. Entradas", digits=(12,2))

    exits             = fields.Float("Salidas (Cant.)", digits=(12,2))
    exits_cost_unit   = fields.Float("Costo Unit. Salidas", digits=(12,2))
    exits_total       = fields.Float("Total Bs. Salidas", digits=(12,2))

    final_stock       = fields.Float("Stock Final", digits=(12,2))
    average_cost      = fields.Float("Costo Promedio", digits=(12,2))
    final_total       = fields.Float("Total Bs. Final", digits=(12,2))
