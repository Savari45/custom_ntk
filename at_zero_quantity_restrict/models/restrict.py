from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import re
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_id = fields.Many2one(
        'product.product',
        domain="[('product_id.qty_available', '>', 0)]",  # Ensures only positive stock products
        required=True
    )
    product_template_id = fields.Many2one(
        'product.template',
        domain="[('qty_available', '>', 0)]",  # Ensures only positive stock products
        required=True
    )

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends('name', 'default_code', 'product_tmpl_id', 'qty_available')
    @api.depends_context('display_default_code', 'seller_id', 'company_id', 'partner_id')
    def _compute_display_name(self):

        def get_display_name(name, code, qty):
            qty_display = f" -- Available: {qty}" if qty is not None else ""
            if self._context.get('display_default_code', True) and code:
                return f'[{code}] {name}{qty_display}'
            return f"{name}{qty_display}"

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        self.check_access("read")

        product_template_ids = self.sudo().product_tmpl_id.ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search_fetch(
                [('product_tmpl_id', 'in', product_template_ids), ('partner_id', 'in', partner_ids)],
                ['product_tmpl_id', 'product_id', 'company_id', 'product_name', 'product_code'],
            )
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)

        # Fetch qty_available in batch for performance optimization
        qty_available_dict = {
            rec['id']: rec['qty_available']
            for rec in self.sudo().read(['qty_available'])
        }

        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()
            name = variant and "%s (%s)" % (product.name, variant) or product.name
            qty_available = qty_available_dict.get(product.id, 0)  # Get quantity from precomputed dict

            sellers = self.env['product.supplierinfo'].sudo().browse(self.env.context.get('seller_id')) or []
            if not sellers and partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                if company_id:
                    sellers = [x for x in sellers if x.company_id.id in [company_id, False]]

            if sellers:
                temp = []
                for s in sellers:
                    seller_variant = s.product_name and (
                            variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                    ) or False
                    temp.append(get_display_name(seller_variant or name, s.product_code or product.default_code,
                                                 qty_available))

                product.display_name = ", ".join(set(temp))  # Use set to avoid duplicates
            else:
                product.display_name = get_display_name(name, product.default_code, qty_available)


class ProductTemplate(models.Model):
    _inherit = "product.template"


    @api.depends('name', 'default_code', 'qty_available')
    def _compute_display_name(self):
        for template in self:
            if not template.name:
                template.display_name = False
            else:
                template.display_name = "{} {}--AVAILABLE : {}".format(
                    "[%s] " % template.default_code if template.default_code else "",
                    template.name,
                    int(template.qty_available)  # Convert to integer for cleaner display
                )

