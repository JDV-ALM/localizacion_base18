from odoo import api, SUPERUSER_ID

def post_init_debit_note(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Creamos producto “DIFERENCIAL CAMBIARIO” si no existe
    product = env["product.product"].search([("default_code", "=", "DIF_CAMBIO")], limit=1)
    if not product:
        tax = env["account.tax"].search([
            ("amount", "=", 16.0),
            ("type_tax_use", "=", "sale")
        ], limit=1)
        income_acc = env["account.account"].search([("code", "=", "4102003")], limit=1)
        env["product.product"].create({
            "name": "DIFERENCIAL CAMBIARIO",
            "type": "service",
            "default_code": "DIF_CAMBIO",
            "sale_ok": True,
            "purchase_ok": False,
            "list_price": 0.0,
            "taxes_id": [(6, 0, tax.ids)] if tax else [],
            "property_account_income_id": income_acc.id if income_acc else False,
        })
