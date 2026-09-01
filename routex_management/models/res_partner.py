from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    route_customer = fields.Boolean(string="Route Customer")
    route_salesperson_id = fields.Many2one(
        "res.users", string="Route Sales Person"
    )
    route_sales_team = fields.Char(string="Route Sales Team")
    route_visit_count = fields.Integer(
        compute="_compute_route_visit_count"
    )

    def _compute_route_visit_count(self):
        Visit = self.env["routex.route.plan.line"]
        for partner in self:
            partner.route_visit_count = Visit.search_count([
                ("partner_id", "=", partner.id)
            ])
