from odoo import fields, models


class RouteXConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    route_default_salesperson_id = fields.Many2one(
        "res.users",
        string="Default Route Sales Person",
        config_parameter="routex_management.default_salesperson_id",
    )
    route_default_team_leader_id = fields.Many2one(
        "res.users",
        string="Default Route Team Leader",
        config_parameter="routex_management.default_team_leader_id",
    )
    route_system_lock_start = fields.Float(
        string="System Lock Start Time",
        config_parameter="routex_management.system_lock_start",
        default=19.0,
    )
    route_system_lock_end = fields.Float(
        string="System Lock End Time",
        config_parameter="routex_management.system_lock_end",
        default=4.0,
    )
