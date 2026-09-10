# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	message = _("Covers assets placed with external client and partner personnel (FR-77).")
	return columns, data, message

def get_columns():
	return [
		{"label": _("Client / Partner Company"), "fieldname": "holding_company", "fieldtype": "Link", "options": "Tracora Company", "width": 180},
		{"label": _("Contact / Holder"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{"label": _("Employee Code"), "fieldname": "employee", "fieldtype": "Link", "options": "Tracora Employee", "width": 130},
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Serial No"), "fieldname": "serial_no", "fieldtype": "Data", "width": 120},
		{"label": _("Assigned Date"), "fieldname": "assigned_on", "fieldtype": "Date", "width": 110},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "Tracora Location", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
	]

def get_data(filters):
	conditions = ["c.company_type = 'External'"]
	values = {}

	if filters.get("holding_company"):
		conditions.append("a.holding_company = %(holding_company)s")
		values["holding_company"] = filters["holding_company"]
	if filters.get("employee"):
		conditions.append("e.name = %(employee)s")
		values["employee"] = filters["employee"]

	where_clause = " WHERE " + " AND ".join(conditions)

	# STRICT PII EXCLUSION (FR-39): aadhaar_number and permanent_address are NEVER selected!
	query = f"""
		SELECT
			a.holding_company,
			e.employee_name,
			e.name AS employee,
			a.asset_tag,
			a.asset_name,
			a.serial_no,
			a.assigned_on,
			a.location,
			a.status
		FROM `tabTracora Asset` a
		JOIN `tabTracora Company` c ON a.holding_company = c.name
		LEFT JOIN `tabTracora Employee` e ON a.assigned_to = e.name
		{where_clause}
		ORDER BY a.holding_company ASC, a.name ASC
	"""
	return frappe.db.sql(query, values, as_dict=True)
