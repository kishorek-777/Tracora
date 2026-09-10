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
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Tracora Branch", "width": 140},
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Tracora Brand", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Condition"), "fieldname": "condition", "fieldtype": "Data", "width": 100},
		{"label": _("Assigned To"), "fieldname": "assigned_to", "fieldtype": "Link", "options": "Tracora Employee", "width": 140},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "Tracora Location", "width": 130},
	]

def get_data(filters):
	conditions = []
	values = {}

	if filters.get("branch"):
		conditions.append("a.branch = %(branch)s")
		values["branch"] = filters["branch"]
	if filters.get("holding_company"):
		conditions.append("a.holding_company = %(holding_company)s")
		values["holding_company"] = filters["holding_company"]
	if filters.get("status"):
		conditions.append("a.status = %(status)s")
		values["status"] = filters["status"]

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

	query = f"""
		SELECT
			COALESCE(a.branch, 'Unassigned Branch') AS branch,
			a.asset_tag,
			a.asset_name,
			a.brand,
			a.status,
			a.condition,
			a.assigned_to,
			a.location
		FROM `tabTracora Asset` a
		{where_clause}
		ORDER BY a.branch ASC, a.name ASC
	"""
	return frappe.db.sql(query, values, as_dict=True)
