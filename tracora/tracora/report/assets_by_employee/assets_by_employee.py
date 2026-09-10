# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	message = _("Covers internal company employees only (FR-77). For client/partner-placed assets, see the External Custody report.")
	return columns, data, message

def get_columns():
	return [
		{"label": _("Employee Code"), "fieldname": "employee", "fieldtype": "Link", "options": "Tracora Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Tracora Company", "width": 140},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Tracora Department", "width": 130},
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Serial No"), "fieldname": "serial_no", "fieldtype": "Data", "width": 120},
		{"label": _("Assigned Date"), "fieldname": "assigned_on", "fieldtype": "Date", "width": 110},
		{"label": _("Asset Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Employee Status"), "fieldname": "employee_status", "fieldtype": "Data", "width": 170},
	]

def get_data(filters):
	conditions = ["c.company_type = 'Internal'"]
	values = {}

	if filters.get("company"):
		conditions.append("e.company = %(company)s")
		values["company"] = filters["company"]
	if filters.get("department"):
		conditions.append("e.department = %(department)s")
		values["department"] = filters["department"]
	if filters.get("employee"):
		conditions.append("e.name = %(employee)s")
		values["employee"] = filters["employee"]

	where_clause = " WHERE " + " AND ".join(conditions)

	# STRICT PII EXCLUSION (FR-39): aadhaar_number and permanent_address are NEVER selected!
	query = f"""
		SELECT
			e.name AS employee,
			e.employee_name,
			e.company,
			e.department,
			a.asset_tag,
			a.asset_name,
			a.serial_no,
			a.assigned_on,
			a.status,
			e.status AS employee_status
		FROM `tabTracora Asset` a
		JOIN `tabTracora Employee` e ON a.assigned_to = e.name
		JOIN `tabTracora Company` c ON e.company = c.name
		{where_clause}
		ORDER BY e.name ASC, a.name ASC
	"""
	return frappe.db.sql(query, values, as_dict=True)
