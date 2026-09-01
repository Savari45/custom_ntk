from odoo import api, fields, models


class RouteXRoute(models.Model):
    _name = "routex.route"
    _description = "Route"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, copy=False)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    area_id = fields.Many2one(
        "routex.route.area", string="Route Area",
        required=True, ondelete="restrict"
    )
    salesperson_id = fields.Many2one("res.users", string="Default Sales Person")
    sales_team = fields.Char(string="Sales Team")

    line_ids = fields.One2many(
        "routex.route.line", "route_id", string="Customers", copy=True
    )
    customer_count = fields.Integer(compute="_compute_customer_count")

    company_id = fields.Many2one(
        "res.company", related="area_id.company_id", store=True, readonly=True
    )

    _sql_constraints = [
        ("code_company_uniq", "unique(code, company_id)",
         "Route code must be unique per company.")
    ]

    @api.depends("line_ids")
    def _compute_customer_count(self):
        for rec in self:
            rec.customer_count = len(rec.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code") in (False, "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code(
                    "routex.route"
                ) or "New"
        return super().create(vals_list)


class RouteXRouteLine(models.Model):
    _name = "routex.route.line"
    _description = "Route Customer"
    _order = "sequence, id"

    route_id = fields.Many2one(
        "routex.route", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(default=10)
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        domain="[('route_customer', '=', True)]"
    )
    description = fields.Char()
    planned_minutes = fields.Integer(default=30)

    _sql_constraints = [
        ("route_customer_uniq", "unique(route_id, partner_id)",
         "The same customer cannot be added twice to a route.")
    ]
