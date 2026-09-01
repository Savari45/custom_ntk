{
    "name": "RouteX",
    "version": "18.0.1.0.0",
    "category": "Sales",
    "summary": "Standalone customer route planning and visit management",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["base",'fleet','hr'],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/cron.xml",
        "views/route_plan_template_views.xml",
        "views/route_plan_views.xml",
        "views/route_plan_line_views.xml",
        "views/res_partner_views.xml",
        "views/visit_cancellation_reason_views.xml",
        "views/res_config_settings_views.xml",
        "views/menu.xml",
        "report/route_plan_report.xml"
    ],
    "installable": True,
    "application": True
}
