# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Holding Company"), "fieldname": "holding_company", "fieldtype": "Link", "options": "Tracora Company", "width": 150},
		{"label": _("Owner Company (Ownership)"), "fieldname": "owner_company", "fieldtype": "Link", "options": "Tracora Company", "width": 180},
		{"label": _("Assigned To"), "fieldname": "assigned_to", "fieldtype": "Link", "options": "Tracora Employee", "width": 140},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Tracora Branch", "width": 130},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "Tracora Location", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
	]

def get_data(filters):
	conditions = []
	values = {}

	if filters.get("holding_company"):
		conditions.append("a.holding_company = %(holding_company)s")
		values["holding_company"] = filters["holding_company"]
	if filters.get("status"):
		conditions.append("a.status = %(status)s")
		values["status"] = filters["status"]

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

	query = f"""
		SELECT
			a.asset_tag,
			a.asset_name,
			a.holding_company,
			a.owner_company,
			a.assigned_to,
			a.branch,
			a.location,
			a.status
		FROM `tabTracora Asset` a
		{where_clause}
		ORDER BY a.holding_company ASC, a.name ASC
	"""
	return frappe.db.sql(query, values, as_dict=True)
