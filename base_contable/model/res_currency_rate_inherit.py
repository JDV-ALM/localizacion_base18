# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import timedelta, date, datetime
from odoo.exceptions import UserError

from pytz import timezone
from bs4 import BeautifulSoup
import requests
import urllib3
urllib3.disable_warnings()
#Moneda..
class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    _sql_constraints = [('unique_name', 'CHECK(1=1)', 'Only one currency rate per day allowed!')]
    #currency_id = fields.Many2one('res.currency',readonly=False,copied=False)


    def central_bank(self):
        url = "https://www.bcv.org.ve/"
        req = requests.get(url, verify=False)

        status_code = req.status_code
        if status_code == 200:

            html = BeautifulSoup(req.text, "html.parser")
            # Dolar
            dolar = html.find('div', {'id': 'dolar'})
            dolar = str(dolar.find('strong')).split()
            dolar = str.replace(dolar[1], '.', '')
            dolar = float(str.replace(dolar, ',', '.'))
            # Euro
            euro = html.find('div', {'id': 'euro'})
            euro = str(euro.find('strong')).split()
            euro = str.replace(euro[1], '.', '')
            euro = float(str.replace(euro, ',', '.'))

            if self.currency_id.name == 'USD':
                bcv = dolar
            elif self.currency_id.name == 'EUR':
                bcv = euro
            else:
                bcv = False
            #raise UserError(_("valor=%s")%dolar) 

            lista=self.env['res.company'].search([])
            #for det in lista:
            ##dolar=60
            vals=({
                        #'hora':datetime.now(),
                'name':datetime.now(),
                'inverse_company_rate':dolar,
                'currency_id':1,
                'company_rate':1/dolar,
                'company_id':'', #det.id, #self.env.company.id #det.id,
                })
            self.create(vals)
            self.funcion_actualiza_coste_precio_venta()

    def funcion_actualiza_coste_precio_venta(self):
        lista2=self.env['product.product'].search([])
        if lista2:
            for item in lista2:
                item.actualiza_coste()
                item.actualiza_precio_venta_bs()

        lista=self.env['product.template'].search([])
        if lista:
            for rec in lista:
                rec.actualiza_coste()
                rec.actualiza_precio_venta_bs()