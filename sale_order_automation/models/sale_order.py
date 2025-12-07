from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super(SaleOrder, self.with_context(default_immediate_transfer=True)).action_confirm()
        for order in self:
            if not order.order_line:
                raise UserError(_("You cannot confirm a Sale Order without any products."))

            zero_price_lines = order.order_line.filtered(
                lambda line: line.price_unit <= 0 or line.price_subtotal <= 0
            )
            if zero_price_lines:
                raise UserError(_("You cannot confirm a Sale Order with zero-priced products."))

            warehouse = order.warehouse_id

            # Process delivery order
            if warehouse.is_delivery_set_to_done and order.picking_ids:
                for picking in order.picking_ids:
                    if picking.state == 'cancel':
                        continue
                    for move in picking.move_ids:
                        move.quantity = move.product_qty
                    picking._autoconfirm_picking()
                    picking.button_validate()
                    for move_line in picking.move_ids_without_package:
                        move_line.quantity = move_line.product_uom_qty
                    for mv_line in picking.move_ids.mapped('move_line_ids'):
                        mv_line.quantity = mv_line.quantity_product_uom
                    picking._action_done()

            # Create invoice if required
            if warehouse.create_invoice and not order.invoice_ids:
                order._create_invoices()

            # Apply cash rounding and post invoice
            if warehouse.validate_invoice and order.invoice_ids:
                for invoice in order.invoice_ids:
                    if not invoice.invoice_cash_rounding_id:
                        rounding = self.env['account.cash.rounding'].search([], limit=1)
                        if rounding:
                            invoice.invoice_cash_rounding_id = rounding.id
                            invoice._recompute_cash_rounding_lines()
                    invoice.action_post()

        return res
