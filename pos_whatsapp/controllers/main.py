# controllers/main.py
from odoo import http
from odoo.http import request, content_disposition
import base64
import logging

_logger = logging.getLogger(__name__)


class PosWhatsAppController(http.Controller):

    @http.route('/pos/whatsapp_receipt', type='json', auth='user', methods=['POST'])
    def generate_receipt_pdf(self, order_id, **kwargs):
        _logger.info("Generating PDF receipt for order %s", order_id)
        try:
            order = request.env['pos.order'].browse(int(order_id)).sudo()
            if not order.exists():
                return {'error': 'Order not found'}

            pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'pos_sale.report_invoice_document',
                order.ids
            )

            attachment = request.env['ir.attachment'].sudo().create({
                'name': f'Receipt_{order.name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf[0]),
                'res_model': 'pos.order',
                'res_id': order.id,
                'mimetype': 'application/pdf'
            })

            return {
                'url': f'/web/content/{attachment.id}?download=true'
            }

        except Exception as e:
            _logger.error("Failed to generate POS receipt PDF: %s", str(e))
            return {'error': str(e)}