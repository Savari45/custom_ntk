from odoo import api, fields, models
from odoo.exceptions import UserError


class RoutePlanLine(models.Model):
    _name = "routex.route.plan.line"
    _description = "Route Plan Customer Visit"
    _order = "sequence, id"

    plan_id = fields.Many2one(
        "routex.route.plan", required=True, ondelete="cascade"
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

    state = fields.Selection(
        [
            ("planned", "Planned"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("skipped", "Skipped"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="planned",
        required=True
    )

    start_on = fields.Datetime(readonly=True)
    end_on = fields.Datetime(readonly=True)
    total_time = fields.Float(
        compute="_compute_total_time", store=True,
        help="Visit duration in hours."
    )
    cancellation_reason_id = fields.Many2one(
        "routex.visit.cancellation.reason",
        string="Cancellation Reason",
        ondelete="restrict",
    )
    cancellation_reason = fields.Text(
        string="Cancellation Notes",
    )
    visit_notes = fields.Text()

    latitude = fields.Float(digits=(10, 7))
    longitude = fields.Float(digits=(10, 7))

    payment_collected = fields.Monetary()
    currency_id = fields.Many2one(
        "res.currency",
        related="plan_id.currency_id",
        readonly=True
    )

    salesperson_id = fields.Many2one(
        "res.users", related="plan_id.salesperson_id",
        store=True, readonly=True
    )
    team_leader_id = fields.Many2one(
        "res.users", related="plan_id.team_leader_id",
        store=True, readonly=True
    )
    scheduled_date = fields.Date(
        related="plan_id.scheduled_date", store=True, readonly=True
    )
    company_id = fields.Many2one(
        "res.company", related="plan_id.company_id",
        store=True, readonly=True
    )

    @api.depends("start_on", "end_on")
    def _compute_total_time(self):
        for rec in self:
            if rec.start_on and rec.end_on:
                rec.total_time = (
                    rec.end_on - rec.start_on
                ).total_seconds() / 3600.0
            else:
                rec.total_time = 0.0

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.latitude = rec.partner_id.partner_latitude
                rec.longitude = rec.partner_id.partner_longitude

    def _check_salesperson(self):
        for rec in self:
            if self.env.user.has_group(
                "routex_management.group_route_manager"
            ):
                continue
            if rec.salesperson_id != self.env.user:
                raise UserError(
                    "You can only operate your own customer visits."
                )

    def action_start(self):
        self._check_salesperson()
        for rec in self:
            if rec.plan_id.state == "planned":
                rec.plan_id.action_start()
            if rec.plan_id.state != "in_progress":
                raise UserError("The route must be In Progress.")
            if rec.state != "planned":
                raise UserError("Only Planned visits can be started.")
            rec.write({
                "state": "in_progress",
                "start_on": fields.Datetime.now()
            })

    def action_done(self):
        self._check_salesperson()
        for rec in self:
            if rec.state != "in_progress":
                raise UserError(
                    "Start the customer visit before clicking Done."
                )
            rec.write({
                "state": "completed",
                "end_on": fields.Datetime.now()
            })

    def action_skip(self):
        self._check_salesperson()
        for rec in self:
            if rec.state not in ("planned", "in_progress"):
                raise UserError(
                    "Only Planned or In Progress visits can be skipped."
                )
            if not rec.cancellation_reason_id:
                raise UserError(
                    "Please select a Visit Cancellation Reason before skipping."
                )
            rec.write({
                "state": "skipped",
                "end_on": fields.Datetime.now()
            })

    def _check_approver(self):
        if self.env.user.has_group(
            "routex_management.group_route_manager"
        ):
            return
        for rec in self:
            if not self.env.user.has_group(
                "routex_management.group_route_team_leader"
            ):
                raise UserError(
                    "Only a Team Leader or Route Manager can approve."
                )
            if rec.team_leader_id and rec.team_leader_id != self.env.user:
                raise UserError(
                    "Only the assigned Team Leader can approve this visit."
                )

    def action_approve(self):
        self._check_approver()
        for rec in self:
            if rec.state != "completed":
                raise UserError("Only Completed visits can be approved.")
            rec.state = "approved"

    def action_reject(self):
        self._check_approver()
        for rec in self:
            if rec.state != "completed":
                raise UserError("Only Completed visits can be rejected.")
            rec.state = "rejected"

    def action_reopen(self):
        if not self.env.user.has_group(
            "routex_management.group_route_manager"
        ):
            raise UserError("Only Route Manager can reopen a visit.")
        self.write({
            "state": "planned",
            "start_on": False,
            "end_on": False
        })
