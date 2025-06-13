# -*- coding: utf-8 -*-

from . import models
from . import wizard

def post_init_hook(env):
    """Post-installation hook to configure Venezuelan localization defaults"""
    # Set up default Venezuelan chart of accounts configurations
    companies = env['res.company'].search([])
    for company in companies:
        # Configure default Venezuelan settings if not already set
        if not company.country_id:
            venezuela = env['res.country'].search([('code', '=', 'VE')], limit=1)
            if venezuela:
                company.country_id = venezuela.id
        
        # Set default currency to VES if available
        ves_currency = env['res.currency'].search([('name', '=', 'VES')], limit=1)
        if ves_currency and not company.currency_id:
            company.currency_id = ves_currency.id