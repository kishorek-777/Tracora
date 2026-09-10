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
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 160},
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Tracora Brand", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Assigned To"), "fieldname": "assigned_to", "fieldtype": "Link", "options": "Tracora Employee", "width": 140},
	]

def get_data(filters):
	conditions = []
	values = {}

	if filters.get("department"):
		conditions.append("e.department = %(department)s")
		values["department"] = filters["department"]
	if filters.get("holding_company"):
		conditions.append("a.holding_company = %(holding_company)s")
		values["holding_company"] = filters["holding_company"]

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

	query = f"""
		SELECT
			COALESCE(e.department, 'Unassigned Stock') AS department,
			a.asset_tag,
			a.asset_name,
			a.brand,
			a.status,
			a.assigned_to
		FROM `tabTracora Asset` a
		LEFT JOIN `tabTracora Employee` e ON a.assigned_to = e.name
		{where_clause}
		ORDER BY CASE WHEN e.department IS NULL THEN 1 ELSE 0 END, e.department ASC, a.name ASC
	"""
	return frappe.db.sql(query, values, as_dict=True)
