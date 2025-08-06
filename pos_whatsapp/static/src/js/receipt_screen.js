/** @odoo-module **/

import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { formatMonetary } from "@web/views/fields/formatters";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        this.notification = this.env.services.notification;
    },

    async onCustomButton() {
        if (!this.pos.config.send_whatsapp) {
            this.notification.add(_t('WhatsApp sending is disabled in this POS config.'), {
                type: 'warning',
                timeout: 3000
            });
            return;
        }

        const order = this.currentOrder;
        const partner = order.get_partner();

        if (!partner || !partner.mobile) {
            this.notification.add(_t('Customer mobile number missing'), {
                type: 'warning',
                sticky: false
            });
            return;
        }

        try {
            const phone = partner.mobile.replace(/\D/g, '');
            const currency = this.pos.currency;
            const total = formatMonetary(order.get_total_with_tax(), { currency });
            const subtotal = formatMonetary(order.get_total_without_tax(), { currency });
            const date = new Date().toLocaleString();
            const companyName = this.pos.company ? this.pos.company.name : '';

            // Build product details
            let productLines = '';
            let totalQuantity = 0;

            const orderLines = order.get_orderlines ? order.get_orderlines() : (order.orderlines || []);

            for (const line of orderLines) {
                if (!line) continue;

                // Try different ways to access the product
                const product = line.product ||
                              (line.get_product ? line.get_product() : null) ||
                              (line.product_id && this.pos.db.get_product_by_id(line.product_id));

                if (!product) {
                    console.log('Could not find product for line:', line);
                    continue;
                }

                const name = product.display_name || product.name || _t('Unnamed');

                // FIX: Properly access quantity - try different methods
                const quantity = line.quantity ||
                               (line.get_quantity ? line.get_quantity() : 0) ||
                               0;

                totalQuantity += Number(quantity) || 0; // Ensure we have a number

                const unitPrice = line.get_unit_price ? line.get_unit_price() : 0;
                const lineTotal = line.get_price_with_tax ? line.get_price_with_tax() : 0;
                const priceWithoutTax = line.get_price_without_tax ? line.get_price_without_tax() : 0;

                // Discount information
                const discountAmount = (unitPrice * quantity) - priceWithoutTax;
                const discount = line.discount ?
                    `\n   ${_t('Discount')}: ${line.discount}% (${formatMonetary(discountAmount, { currency })})` :
                    '';

                // Tax information
                let taxInfo = '';
                const taxes = line.get_taxes ? line.get_taxes() : [];
                const totalTaxAmount = lineTotal - priceWithoutTax;
                const taxPercent = taxes.length > 0 ? taxes.reduce((sum, tax) => sum + tax.amount, 0) : 0;

                if (taxes.length > 0) {
                    taxInfo = `\n   ${_t('Tax')}: ${taxPercent.toFixed(2)}% (${formatMonetary(totalTaxAmount, { currency })})`;
                }

                productLines += `• ${name} x${quantity} - ${formatMonetary(unitPrice, { currency })} = ${formatMonetary(lineTotal, { currency })}${discount}${taxInfo}\n`;
            }

            // Order summary
            const totalDiscount = order.get_total_discount ? order.get_total_discount() : 0;
            const totalTax = order.get_total_with_tax() - order.get_total_without_tax();
            const taxRate = order.get_total_without_tax() > 0 ?
                (totalTax / order.get_total_without_tax() * 100).toFixed(2) :
                '0.00';

            const message = `
Hi ${partner.name || _t('Valued Customer')},

Your order details from ${companyName}:

 Order Number: ${order.name}
 Date: ${date}

 Products (${totalQuantity} items):
${productLines || 'No products in order'}

 Order Summary:
Subtotal: ${subtotal}
${totalDiscount > 0 ? `Total Discount: ${formatMonetary(totalDiscount, { currency })}\n` : ''}
Including Tax
 Total Amount: ${total}

Thank you for your purchase!
            `.trim();

            const url = `https://web.whatsapp.com/send?phone=${phone}&text=${encodeURIComponent(message)}`;
            window.open(url, '_blank');

            this.notification.add(_t('Opening WhatsApp Web...'), {
                type: 'info',
                sticky: false
            });

        } catch (error) {
            this.notification.add(_t('Failed to open WhatsApp: ') + error.message, {
                type: 'danger',
                sticky: false
            });
            console.error('WhatsApp error:', error);
        }
    }
});
