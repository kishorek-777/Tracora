# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	return columns, data, None, chart

def get_columns():
	return [
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Tracora Brand", "width": 120},
		{"label": _("Serial No"), "fieldname": "serial_no", "fieldtype": "Data", "width": 130},
		{"label": _("Owner Company"), "fieldname": "owner_company", "fieldtype": "Link", "options": "Tracora Company", "width": 150},
		{"label": _("Holding Company"), "fieldname": "holding_company", "fieldtype": "Link", "options": "Tracora Company", "width": 150},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Tracora Branch", "width": 130},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "Tracora Location", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Condition"), "fieldname": "condition", "fieldtype": "Data", "width": 100},
	]

def get_data(filters):
	conditions = []
	values = {}

	if filters.get("owner_company"):
		conditions.append("a.owner_company = %(owner_company)s")
		values["owner_company"] = filters["owner_company"]
	if filters.get("status"):
		conditions.append("a.status = %(status)s")
		values["status"] = filters["status"]
	if filters.get("condition"):
		conditions.append("a.condition = %(condition)s")
		values["condition"] = filters["condition"]

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

	query = f"""
		SELECT
			a.asset_tag,
			a.asset_name,
			a.brand,
			a.serial_no,
			a.owner_company,
			a.holding_company,
			a.branch,
			a.location,
			a.status,
			a.condition
		FROM `tabTracora Asset` a
		{where_clause}
		ORDER BY a.owner_company ASC, a.name ASC
	"""
	return frappe.db.sql(query, values, as_dict=True)

def get_chart(data):
	if not data:
		return None

	counts_by_company = {}
	for row in data:
		co = row.get("owner_company") or "Unknown"
		counts_by_company[co] = counts_by_company.get(co, 0) + 1

	return {
		"data": {
			"labels": list(counts_by_company.keys()),
			"datasets": [
				{"name": _("Owned Assets"), "values": list(counts_by_company.values())}
			]
		},
		"type": "bar",
		"colors": ["#3182ce"]
	}
