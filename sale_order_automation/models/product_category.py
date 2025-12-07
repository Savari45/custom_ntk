from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import re
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
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

    sub_categ_id = fields.Many2one(
        'product.category', 'Product Sub Category')
    a_percentage = fields.Float(string="A (%)", store=True)
    b_percentage = fields.Float(string="B (%)", store=True)
    c_percentage = fields.Float(string="C (%)", store=True)
    d_percentage = fields.Float(string="D (%)", store=True)

    margin_percentage = fields.Float(
        string="Margin (%)",
        compute="_compute_margin_percentage",
        store=True
    )

    @api.depends('standard_price', 'list_price')
    def _compute_margin_percentage(self):
        """ Calculate the margin percentage """
        for product in self:
            if product.standard_price is None or product.standard_price <= 0:
                product.margin_percentage = 0.0
            elif product.list_price:  # Avoid division by zero
                product.margin_percentage = ((product.list_price - product.standard_price) / product.list_price) * 100
            else:
                product.margin_percentage = 0.0

    @api.onchange('margin_percentage')
    def _onchange_margin_percentage(self):
        """ Automatically update sub-category based on margin percentage and defined thresholds """
        categories = self.env['product.category'].search([('name', 'in', ['A', 'B', 'C', 'D'])])

        # Create a dictionary for category lookup
        category_map = {cat.name: cat.id for cat in categories}

        for product in self:
            if product.margin_percentage >= product.a_percentage and 'A' in category_map:
                product.sub_categ_id = category_map['A']  # Margin >= A → Category A
            elif product.b_percentage <= product.margin_percentage < product.a_percentage and 'B' in category_map:
                product.sub_categ_id = category_map['B']  # B ≤ Margin < A → Category B
            elif product.c_percentage <= product.margin_percentage < product.b_percentage and 'C' in category_map:
                product.sub_categ_id = category_map['C']  # C ≤ Margin < B → Category C
            elif product.margin_percentage < product.c_percentage and 'D' in category_map:
                product.sub_categ_id = category_map['D']  # Margin < C → Category D
            else:
                product.sub_categ_id = False  # No valid category found, reset it

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

