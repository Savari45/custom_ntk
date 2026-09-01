from odoo import fields, models


class RouteVisitCancellationReason(models.Model):
    _name = "routex.visit.cancellation.reason"
    _description = "Visit Cancellation Reason"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    note = fields.Text()

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name)",
            "Cancellation reason must be unique."
        )
    ]
