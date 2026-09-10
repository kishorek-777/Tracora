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
		{"label": _("Renewal Cycle"), "fieldname": "renewal_cycle", "fieldtype": "Data", "width": 120},
		{"label": _("Next Renewal Due"), "fieldname": "next_renewal_date", "fieldtype": "Date", "width": 130},
		{"label": _("Days Until Renewal"), "fieldname": "days_until_renewal", "fieldtype": "Int", "width": 140},
		{"label": _("Status"), "fieldname": "licence_status", "fieldtype": "Data", "width": 120},
	]

def get_data(filters):
	conditions = []
	values = {}

	# Handle NULL next_renewal_date cleanly
	if not filters.get("include_non_renewing"):
		conditions.append("l.next_renewal_date IS NOT NULL")

	if filters.get("company"):
		conditions.append("l.company = %(company)s")
		values["company"] = filters["company"]
	if filters.get("renewal_cycle"):
		conditions.append("l.renewal_cycle = %(renewal_cycle)s")
		values["renewal_cycle"] = filters["renewal_cycle"]

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

	# Pure query using next_renewal_date and renewal_cycle (payment_date/licence_renewal_date DO NOT EXIST)
	query = f"""
		SELECT
			l.software_name,
			l.name AS licence_name,
			l.company,
			l.renewal_cycle,
			l.next_renewal_date,
			CASE
				WHEN l.next_renewal_date IS NOT NULL THEN DATEDIFF(l.next_renewal_date, CURDATE())
				ELSE NULL
			END AS days_until_renewal,
			l.licence_status
		FROM `tabTracora Software Licence` l
		{where_clause}
		ORDER BY CASE WHEN l.next_renewal_date IS NULL THEN 1 ELSE 0 END, l.next_renewal_date ASC, l.name ASC
	"""
	return frappe.db.sql(query, values, as_dict=True)
