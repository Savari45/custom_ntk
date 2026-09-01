from odoo import api, fields, models
from odoo.exceptions import UserError


class RoutePlan(models.Model):
    _name = "routex.route.plan"
    _description = "Route Plan"
    _order = "scheduled_date desc, id desc"

    name = fields.Char(
        string="Reference", required=True, copy=False,
        default="New", readonly=True
    )
    template_id = fields.Many2one(
        "routex.route.plan.template", readonly=True
    )

    salesperson_id = fields.Many2one(
        "res.users", string="Sales Person",
        required=True, default=lambda self: self.env.user
    )
    sales_team = fields.Char(string="Sales Team")
    team_leader_id = fields.Many2one(
        "res.users", string="Team Leader",
        help="User who approves customer visits for this route."
    )

    vehicle_id = fields.Many2one("fleet.vehicle",string="Vehicle")
    driver_id = fields.Many2one("hr.employee",string="Driver")
    helper_id = fields.Many2one("hr.employee",string="Helper")

    route_ids = fields.Many2many(
        "res.partner.category",
        string="Routes",
    )
    scheduled_date = fields.Date(
        required=True, default=fields.Date.context_today
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("planned", "Planned"),
            ("in_progress", "In Progress"),
            ("complete", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True
    )

    line_ids = fields.One2many(
        "routex.route.plan.line", "plan_id",
        string="Routes", copy=True
    )

    cash_amount = fields.Monetary(string="Cash Amount")
    cheque_amount = fields.Monetary(string="Cheque Amount")
    bank_transfer_amount = fields.Monetary(string="Bank Transfer Amount")
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True
    )

    meter_reading_start = fields.Float(string="Meter Reading Start")
    meter_reading_end = fields.Float(string="Meter Reading End")
    start_image = fields.Binary(string="Start Image", attachment=True)
    end_image = fields.Binary(string="End Image", attachment=True)

    started_at = fields.Datetime(readonly=True)
    ended_at = fields.Datetime(readonly=True)
    notes = fields.Text()

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    customer_count = fields.Integer(compute="_compute_counts")
    planned_count = fields.Integer(compute="_compute_counts")
    in_progress_count = fields.Integer(compute="_compute_counts")
    completed_count = fields.Integer(compute="_compute_counts")
    skipped_count = fields.Integer(compute="_compute_counts")
    pending_approval_count = fields.Integer(compute="_compute_counts")
    approved_count = fields.Integer(compute="_compute_counts")
    rejected_count = fields.Integer(compute="_compute_counts")

    sale_order_count = fields.Integer(string="Sale Orders",compute="_compute_document_counts",)
    invoice_count = fields.Integer(string="Invoices",compute="_compute_document_counts",)
    collection_count = fields.Integer(string="Collections",compute="_compute_document_counts",)
    delivery_count = fields.Integer(string="Deliveries",compute="_compute_document_counts",)

    @api.depends("line_ids.partner_id")
    def _compute_document_counts(self):
        SaleOrder = self.env["sale.order"]
        AccountMove = self.env["account.move"]
        AccountPayment = self.env["account.payment"]
        StockPicking = self.env["stock.picking"]

        for rec in self:
            partners = rec.line_ids.mapped("partner_id")
            rec.sale_order_count = SaleOrder.search_count([
                ("partner_id", "in", partners.ids),
            ])
            rec.invoice_count = AccountMove.search_count([
                ("partner_id", "in", partners.ids),
                ("move_type", "in", ["out_invoice", "out_refund"]),
            ])
            rec.collection_count = AccountPayment.search_count([
                ("partner_id", "in", partners.ids),
                ("payment_type", "=", "inbound"),
            ])
            rec.delivery_count = StockPicking.search_count([
                ("partner_id", "in", partners.ids),
                ("picking_type_code", "=", "outgoing"),
            ])

    def action_view_sale_orders(self):
        self.ensure_one()
        partners = self.line_ids.mapped("partner_id")
        return {
            "type": "ir.actions.act_window",
            "name": "Sale Orders",
            "res_model": "sale.order",
            "view_mode": "list,form",
            "domain": [
                ("partner_id", "in", partners.ids),
            ],
            "context": {
                "default_partner_id": partners[:1].id if partners else False,
            },
        }

    def action_view_invoices(self):
        self.ensure_one()
        partners = self.line_ids.mapped("partner_id")
        return {
            "type": "ir.actions.act_window",
            "name": "Invoices",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [
                ("partner_id", "in", partners.ids),
                ("move_type", "in", ["out_invoice", "out_refund"]),
            ],
        }

    def action_view_collections(self):
        self.ensure_one()
        partners = self.line_ids.mapped("partner_id")
        return {
            "type": "ir.actions.act_window",
            "name": "Collections",
            "res_model": "account.payment",
            "view_mode": "list,form",
            "domain": [
                ("partner_id", "in", partners.ids),
                ("payment_type", "=", "inbound"),
            ],
        }
    def action_view_deliveries(self):
        self.ensure_one()
        partners = self.line_ids.mapped("partner_id")
        return {
            "type": "ir.actions.act_window",
            "name": "Deliveries",
            "res_model": "stock.picking",
            "view_mode": "list,form",
            "domain": [
                ("partner_id", "in", partners.ids),
                ("picking_type_code", "=", "outgoing"),
            ],
        }

    @api.depends("line_ids.state")
    def _compute_counts(self):
        for rec in self:
            states = rec.line_ids.mapped("state")
            rec.customer_count = len(rec.line_ids)
            rec.planned_count = states.count("planned")
            rec.in_progress_count = states.count("in_progress")
            rec.completed_count = states.count("completed")
            rec.skipped_count = states.count("skipped")
            rec.pending_approval_count = states.count("completed")
            rec.approved_count = states.count("approved")
            rec.rejected_count = states.count("rejected")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name") in (False, "New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "routex.route.plan"
                ) or "New"
        return super().create(vals_list)

    @api.model
    @api.model
    def create_from_template(self, template):
        default_salesperson = self.env["ir.config_parameter"].sudo().get_param(
            "routex_management.default_salesperson_id"
        )

        default_team_leader = self.env["ir.config_parameter"].sudo().get_param(
            "routex_management.default_team_leader_id"
        )

        vals = {
            "template_id": template.id,

            "salesperson_id": template.salesperson_id.id or (
                int(default_salesperson)
                if default_salesperson
                else self.env.user.id
            ),

            "team_leader_id": (
                int(default_team_leader)
                if default_team_leader
                else False
            ),

            "sales_team": template.sales_team,

            # Vehicle / Driver / Helper
            "vehicle_id": template.vehicle_id.id or False,
            "driver_id": template.driver_id.id or False,
            "helper_id": template.helper_id.id or False,

            # Multiple Route Categories
            "route_ids": [(6, 0, template.route_ids.ids)],

            "scheduled_date": fields.Date.context_today(self),

            # Customers
            "line_ids": [
                (0, 0, {
                    "sequence": line.sequence,
                    "partner_id": line.partner_id.id,
                    "description": line.description,
                    "planned_minutes": line.planned_minutes,
                })
                for line in template.line_ids
            ],
        }

        return self.create(vals)

    def action_open(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "routex.route.plan",
            "view_mode": "form",
            "res_id": self.id,
        }

    def action_plan(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError("Add at least one customer before planning.")
            rec.state = "planned"

    def action_start(self):
        for rec in self:
            if rec.state not in ("draft", "planned"):
                raise UserError("Only Draft or Planned routes can be started.")
            if not rec.line_ids:
                raise UserError("There are no customers in this route.")
            rec.write({
                "state": "in_progress",
                "started_at": fields.Datetime.now()
            })

    def action_close(self):
        for rec in self:
            pending = rec.line_ids.filtered(
                lambda line: line.state in (
                    "planned", "in_progress", "completed", "rejected"
                )
            )
            if pending:
                raise UserError(
                    "All customers must be Approved or Skipped before closing."
                )
            rec.write({
                "state": "closed",
                "ended_at": fields.Datetime.now()
            })

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        if not self.env.user.has_group(
            "routex_management.group_route_manager"
        ):
            raise UserError("Only Route Manager can reset a route.")
        self.write({"state": "draft", "started_at": False, "ended_at": False})
        self.line_ids.write({
            "state": "planned",
            "start_on": False,
            "end_on": False
        })
