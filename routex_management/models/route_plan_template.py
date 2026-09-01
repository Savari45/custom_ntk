from dateutil.relativedelta import relativedelta

from odoo import api, fields, models,api,Command
from odoo.exceptions import UserError, ValidationError


class RoutePlanTemplate(models.Model):
    _name = "routex.route.plan.template"
    _description = "Route Plan Template"
    _order = "name"

    name = fields.Char(string="Route Name", required=True)
    active = fields.Boolean(default=True)

    salesperson_id = fields.Many2one(
        "res.users", string="Sales Person",
        required=True, default=lambda self: self.env.user
    )
    sales_team = fields.Char(string="Sales Team")
    vehicle_id = fields.Many2one("fleet.vehicle",string="Vehicle",)
    driver_id = fields.Many2one("hr.employee",string="Driver",domain="[('job_id.name', '=', 'Driver')]")
    helper_id = fields.Many2one("hr.employee",string="Helper",domain="[('job_id.name', '=', 'Helper')]")
    route_ids = fields.Many2many("res.partner.category",string="Routes")
    execute_every = fields.Integer(
        string="Execute Every", default=1, required=True
    )
    interval_type = fields.Selection(
        [("days", "Days"), ("weeks", "Weeks"), ("months", "Months")],
        default="days", required=True
    )
    next_execution_date = fields.Date(
        string="Next Execution Date",
        required=True,
        default=fields.Date.context_today
    )
    last_execution_date = fields.Date(readonly=True)

    line_ids = fields.One2many(
        "routex.route.plan.template.line",
        "template_id",
        string="Routes",
        copy=True
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        copy=False,
    )
    plan_id = fields.Many2one(
        "routex.route.plan",
        string="Route Plan",
        readonly=True,
        copy=False,
    )

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(
                    "Add at least one customer to the route template."
                )
            rec.state = "confirmed"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancelled"

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_plan(self):
        self.ensure_one()

        if self.state != "confirmed":
            raise UserError(
                "You can only plan a confirmed route template."
            )

        if not self.line_ids:
            raise UserError(
                "Add at least one customer to the route template."
            )

        # Prevent duplicate plan creation
        if self.plan_id:
            return self.plan_id.action_open()

        plan = self.env["routex.route.plan"].create_from_template(self)

        today = fields.Date.context_today(self)

        self.write({
            "plan_id": plan.id,
            "last_execution_date": today,
            "next_execution_date": self._next_date(today),
        })

        return plan.action_open()

    @api.constrains("execute_every")
    def _check_execute_every(self):
        for rec in self:
            if rec.execute_every <= 0:
                raise ValidationError("Execute Every must be greater than zero.")

    @api.onchange("route_ids")
    def _onchange_route_ids(self):
        for rec in self:

            partners = self.env["res.partner"].search([
                ("category_id", "in", rec.route_ids.ids),
            ])

            commands = [Command.clear()]

            for sequence, partner in enumerate(partners, ):
                print("ADDING PARTNER:", partner.name)

                commands.append(
                    Command.create({
                        "sequence": sequence,
                        "partner_id": partner.id,
                        "description": False,
                        # "planned_minutes": 30,
                    })
                )

            rec.line_ids = commands

         

    def _next_date(self, value):
        self.ensure_one()
        if self.interval_type == "days":
            return value + relativedelta(days=self.execute_every)
        if self.interval_type == "weeks":
            return value + relativedelta(weeks=self.execute_every)
        return value + relativedelta(months=self.execute_every)



    @api.model
    def _cron_generate_due_templates(self):
        today = fields.Date.context_today(self)
        for template in self.search([
            ("active", "=", True),
            ("next_execution_date", "<=", today),
        ]):
            try:
                template.action_plan()
            except Exception:
                continue


class RoutePlanTemplateLine(models.Model):
    _name = "routex.route.plan.template.line"
    _description = "Route Plan Template Line"
    _order = "sequence, id"

    template_id = fields.Many2one(
        "routex.route.plan.template",
        required=True,
        ondelete="cascade"
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
