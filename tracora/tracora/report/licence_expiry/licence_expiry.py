# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, date_diff, getdate

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": _("Software Name"), "fieldname": "software_name", "fieldtype": "Data", "width": 180},
		{"label": _("Licence Name"), "fieldname": "licence_name", "fieldtype": "Link", "options": "Tracora Software Licence", "width": 180},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Tracora Company", "width": 150},
		{"label": _("Licence Type"), "fieldname": "licence_type", "fieldtype": "Data", "width": 120},
		{"label": _("Licence Expiry"), "fieldname": "licence_expiry_date", "fieldtype": "Date", "width": 120},
		{"label": _("Days Remaining"), "fieldname": "days_remaining", "fieldtype": "Int", "width": 130},
		{"label": _("Active Seats"), "fieldname": "active_seats", "fieldtype": "Int", "width": 110},
		{"label": _("Status"), "fieldname": "licence_status", "fieldtype": "Data", "width": 120},
	]

def get_data(filters):
	conditions = []
	values = {}

	if filters.get("company"):
		conditions.append("l.company = %(company)s")
		values["company"] = filters["company"]
	if filters.get("licence_type"):
		conditions.append("l.licence_type = %(licence_type)s")
		values["licence_type"] = filters["licence_type"]
	if filters.get("licence_status"):
		conditions.append("l.licence_status = %(licence_status)s")
		values["licence_status"] = filters["licence_status"]

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

	# active_seats defined strictly as Active seats per FR-20/FR-86 convention
	query = f"""
		SELECT
			l.software_name,
			l.name AS licence_name,
			l.company,
			l.licence_type,
			l.licence_expiry_date,
			DATEDIFF(l.licence_expiry_date, CURDATE()) AS days_remaining,
			(
				SELECT COUNT(*)
				FROM `tabTracora Licence Seat` s
				WHERE s.parent = l.name AND s.seat_status = 'Active'
			) AS active_seats,
			l.licence_status
		FROM `tabTracora Software Licence` l
		{where_clause}
		ORDER BY l.licence_expiry_date ASC, l.name ASC
	"""
	return frappe.db.sql(query, values, as_dict=True)
