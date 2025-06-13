# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import models, fields, _
from odoo.exceptions import UserError
import base64
from io import StringIO
import logging

_logger = logging.getLogger(__name__)

def tipo_format(valor):
    if valor and valor == 'in_refund':
        return '03'
    return '01'

def float_format(valor):
    if valor:
        return '{:,.2f}'.format(valor).replace(',', '')
    return valor

def float_format2(valor):
    if valor:
        return '{:,.2f}'.format(valor).replace(',', '')
    return "0.00"

def completar_cero(campo, digitos):
    return str(campo).rjust(digitos, ' ')

def formato_periodo(valor):
    fecha = str(valor)
    return fecha[0:4] + fecha[5:7]

def rif_format(partner_id):
    """Devuelve el RIF en formato letra+números, sin guiones ni espacios.
    1) Si el partner tiene doc_tipo válido, lo usamos.
    2) Si el VAT empieza por letra válida, la usamos y quitamos esa letra de los dígitos.
    3) En cualquier otro caso, asumimos 'J' por defecto.
    """
    raw = (partner_id.vat or '').upper().replace(' ', '').replace('-', '')
    # 1) doc_tipo
    tipo = (partner_id.doc_tipo or '').upper()
    if tipo in ['V', 'E', 'G', 'J', 'P', 'C']:
        prefix = tipo
    # 2) vat comienza con letra
    elif raw and raw[0] in ['V', 'E', 'G', 'J', 'P', 'C']:
        prefix = raw[0]
        raw = raw[1:]
    # 3) fallback
    else:
        prefix = 'J'

    # Si raw quedó vacío, devolvemos placeholders
    if not raw.isdigit():
        return prefix + '00000000'
    return prefix + raw

class BsoftContratoReport2(models.TransientModel):
    _name = 'snc.wizard.retencioniva'
    _description = 'Generar archivo TXT de retenciones de IVA'

    date_from = fields.Date(
        string='Fecha de Llegada',
        default=lambda *a: datetime.now().strftime('%Y-%m-%d')
    )
    date_to = fields.Date(
        string='Fecha de Salida',
        default=lambda *a: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    )
    file_data = fields.Binary('Archivo TXT', help="Descarga del TXT generado")
    file_name = fields.Char(size=256, string='Nombre de archivo')

    def show_view(self, name, model, id_xml, res_id=None, view_mode='tree,form', nodestroy=True, target='new'):
        ctx = dict(self._context or {})
        ctx.update({'active_model': model})
        return {
            'name': name,
            'view_type': 'form',
            'view_mode': self.env.ref(id_xml).type,
            'view_id': self.env.ref(id_xml).id,
            'res_model': model,
            'res_id': res_id,
            'nodestroy': nodestroy,
            'target': target,
            'type': 'ir.actions.act_window',
            'context': ctx,
        }

    def conv_div(self, move, valor):
        if move.company_id.currency_id != move.currency_id:
            tasa = self.env['account.move'].browse(move.id).tasa
            rate = round(tasa, 3)
            return valor * rate
        return valor

    def action_generate_txt(self):
        # 1) Obtener facturas/receipts retenidas
        moves = self.env['account.move'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('move_type', 'in', ('in_invoice', 'in_refund', 'in_receipt')),
            ('state', '=', 'posted'),
        ], order='date asc')

        # 2) Preparamos buffer en memoria
        buf = StringIO()

        # 3) Volcamos cada línea al buffer con lista de 16 campos
        for move in moves:
            if not move.vat_ret_id or move.vat_ret_id.state != 'posted':
                continue

            # Tipo de documento SENIAT
            if move.move_type == 'in_invoice':
                trans = '01'
            elif move.move_type == 'in_refund':
                trans = '03'
            else:
                trans = '02'

            # Acumulados
            acum_exento = sum(l.base_exenta for l in move.alicuota_line_ids if l.invoice_id == move)
            base_general = sum(l.base_general for l in move.alicuota_line_ids if l.invoice_id == move)

            # Líneas de retención
            lines = self.env['vat.retention.invoice.line'].search([
                ('retention_id', '=', move.vat_ret_id.id)
            ])
            for rec in lines:
                if rec.tax_id.aliquot == 'exempt':
                    continue

                campos = [
                    # A: RIF del Agente de Retención
                    rif_format(move.company_id.partner_id),
                    # B: Periodo Impositivo (AAAAMM)
                    formato_periodo(self.date_to),
                    # C: Fecha de Factura (YYYY-MM-DD)
                    str(move.date),
                    # D: Tipo de Operación (C=compras)
                    'C',
                    # E: Tipo de documento (01=Factura,02=N. Débito,03=N. Crédito)
                    trans,
                    # F: RIF de Proveedor
                    rif_format(move.partner_id),
                    # G: Número de Documento
                    str(move.invoice_number_next),
                    # H: Número de Control
                    str(move.invoice_number_control),
                    # I: Monto total del documento
                    float_format2(abs(move.amount_total_signed)),
                    # J: Base Imponible
                    float_format2(self.conv_div(move, base_general)),
                    # K: Monto del IVA Retenido
                    float_format2(move.vat_ret_id.vat_retentioned),
                    # L: Número del doc. afectado (origen N/D o N/C)
                    (move.ref or '0'),
                    # M: Número de Comprobante de Retención
                    str(move.vat_ret_id.name),
                    # N: Monto Exento del IVA
                    float_format2(self.conv_div(move, acum_exento)),
                    # O: Alícuota (porcentaje)
                    str(round(rec.tax_id.amount)),
                    # P: Número de Expediente (0 si no aplica)
                    '0',
                ]
                buf.write("\t".join(campos) + "\n")

        # 4) Creamos el binary y el nombre de archivo
        content = buf.getvalue()
        buf.close()
        filename = f"Retenciones_IVA_{self.date_from}_a_{self.date_to}.txt"
        data = base64.b64encode(content.encode('utf-8'))

        # 5) Asignamos al wizard para descarga
        self.write({
            'file_data': data,
            'file_name': filename,
        })

        # 6) Forzamos la descarga inmediata
        return {
            'type': 'ir.actions.act_url',
            'url': (
                '/web/content/'
                '?model=snc.wizard.retencioniva'
                f'&id={self.id}'
                '&field=file_data'
                '&filename_field=file_name'
                '&download=true'
            ),
            'target': 'self',
        }
