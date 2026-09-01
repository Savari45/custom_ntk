from odoo import api, fields, models


class RouteArea(models.Model):
    _name = "routex.route.area"
    _description = "Route Area"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    route_ids = fields.One2many("routex.route", "area_id")
    route_count = fields.Integer(compute="_compute_route_count")

    _sql_constraints = [
        ("code_company_uniq", "unique(code, company_id)",
         "Route area code must be unique per company.")
    ]

    @api.depends("route_ids")
    def _compute_route_count(self):
        for rec in self:
            rec.route_count = len(rec.route_ids)
