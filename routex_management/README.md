# RouteX - Standalone Odoo 18

This is a completely standalone module.

Manifest dependency:
- `base` only.

It does NOT depend on:
- OCA route_planning
- CRM
- Sales
- Fleet
- Accounting
- Stock
- Mail
- Any third-party Python package

Main menus:
RouteX
  Customer
    Customers
    Customer Visits
  Management
    Route Plans
    Route Plan Templates
    Visits To Approve
  Reporting
    Route Plans
    Customer Visits
  Configuration
    Route Areas
    Routes
    Route Plan Templates

Main models:
- routex.route.area
- routex.route
- routex.route.line
- routex.route.plan.template
- routex.route.plan.template.line
- routex.route.plan
- routex.route.plan.line

Workflow:
Template -> Plan -> Planned -> In Progress -> Start Customer -> Done -> Completed -> Team Leader Approval -> Approved.

A salesperson clicking Done automatically moves the customer visit to Completed.
Team Leader sees Completed visits in Visits To Approve.
Approve changes the visit to Approved.
Reject changes it to Rejected.
Skipped visits can be skipped directly by the salesperson.

Because this is standalone, route sequencing is managed by the sequence field and there is no OR-Tools/map dependency.
