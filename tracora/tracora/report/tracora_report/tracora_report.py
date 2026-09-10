# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, date_diff, getdate

def execute(filters=None):
	filters = filters or {}
	view = filters.get("primary_view") or "Assets Owned"

	chart = None
	message = None

	if view == "Assets Owned":
		columns, data, chart = get_assets_owned(filters)
	elif view == "Assets Held":
		columns, data = get_assets_held(filters)
	elif view == "Assets by Branch":
		columns, data = get_assets_by_branch(filters)
	elif view == "Assets by Department":
		columns, data = get_assets_by_department(filters)
	elif view == "Assets by Employee":
		columns, data, message = get_assets_by_employee(filters)
	elif view == "External Custody":
		columns, data, message = get_external_custody(filters)
	elif view == "Licence Expiry":
		columns, data = get_licence_expiry(filters)
	elif view == "Licence Renewal Due":
		columns, data = get_licence_renewal_due(filters)
	else:
		columns, data, chart = get_assets_owned(filters)

	# Dynamic column selection filtering if specified
	selected = filters.get("selected_columns")
	if selected:
		if isinstance(selected, str):
			selected = [s.strip() for s in selected.split(",") if s.strip()]
		if isinstance(selected, (list, tuple)) and len(selected) > 0:
			columns = [c for c in columns if c["fieldname"] in selected]

	return columns, data, message, chart

# -------------------------------------------------------------------------
# Helper: Build SQL condition for single or multi-value filter
# -------------------------------------------------------------------------
def add_filter_condition(conditions, values, field_expr, param_name, filter_val):
	if not filter_val:
		return
	if isinstance(filter_val, (list, tuple)):
		# Clean empty strings
		cleaned = [v for v in filter_val if v]
		if not cleaned:
			return
		conditions.append(f"{field_expr} IN %({param_name})s")
		values[param_name] = tuple(cleaned)
	elif isinstance(filter_val, str) and "," in filter_val:
		cleaned = [v.strip() for v in filter_val.split(",") if v.strip()]
		if not cleaned:
			return
		conditions.append(f"{field_expr} IN %({param_name})s")
		values[param_name] = tuple(cleaned)
	else:
		conditions.append(f"{field_expr} = %({param_name})s")
		values[param_name] = filter_val

# -------------------------------------------------------------------------
# 1. Assets Owned
# -------------------------------------------------------------------------
def get_assets_owned(filters):
	columns = [
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Tracora Brand", "width": 120},
		{"label": _("Model Number"), "fieldname": "model_number", "fieldtype": "Data", "width": 130},
		{"label": _("Serial No"), "fieldname": "serial_no", "fieldtype": "Data", "width": 130},
		{"label": _("Owner Company"), "fieldname": "owner_company", "fieldtype": "Link", "options": "Tracora Company", "width": 150},
		{"label": _("Holding Company"), "fieldname": "holding_company", "fieldtype": "Link", "options": "Tracora Company", "width": 150},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Tracora Branch", "width": 130},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "Tracora Location", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Condition"), "fieldname": "condition", "fieldtype": "Data", "width": 100},
	]
	conditions = []
	values = {}

	add_filter_condition(conditions, values, "a.owner_company", "owner_company", filters.get("owner_company") or filters.get("company"))
	add_filter_condition(conditions, values, "a.status", "status", filters.get("status"))
	add_filter_condition(conditions, values, "a.condition", "condition", filters.get("condition"))
	add_filter_condition(conditions, values, "a.branch", "branch", filters.get("branch"))

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
	query = f"""
		SELECT
			a.asset_tag,
			a.asset_name,
			a.brand,
			a.model_number,
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
	data = frappe.db.sql(query, values, as_dict=True)

	chart = None
	if data:
		counts_by_company = {}
		for row in data:
			co = row.get("owner_company") or "Unknown"
			counts_by_company[co] = counts_by_company.get(co, 0) + 1
		chart = {
			"data": {
				"labels": list(counts_by_company.keys()),
				"datasets": [{"name": _("Owned Assets"), "values": list(counts_by_company.values())}]
			},
			"type": "bar",
			"colors": ["#3182ce"]
		}

	return columns, data, chart

# -------------------------------------------------------------------------
# 2. Assets Held
# -------------------------------------------------------------------------
def get_assets_held(filters):
	columns = [
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Holding Company"), "fieldname": "holding_company", "fieldtype": "Link", "options": "Tracora Company", "width": 150},
		{"label": _("Owner Company (Ownership)"), "fieldname": "owner_company", "fieldtype": "Link", "options": "Tracora Company", "width": 180},
		{"label": _("Assigned To"), "fieldname": "assigned_to", "fieldtype": "Link", "options": "Tracora Employee", "width": 140},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Tracora Branch", "width": 130},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "Tracora Location", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
	]
	conditions = []
	values = {}

	add_filter_condition(conditions, values, "a.holding_company", "holding_company", filters.get("holding_company") or filters.get("company"))
	add_filter_condition(conditions, values, "a.status", "status", filters.get("status"))

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
	data = frappe.db.sql(query, values, as_dict=True)
	return columns, data

# -------------------------------------------------------------------------
# 3. Assets by Branch
# -------------------------------------------------------------------------
def get_assets_by_branch(filters):
	columns = [
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Tracora Branch", "width": 130},
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Tracora Brand", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Condition"), "fieldname": "condition", "fieldtype": "Data", "width": 100},
		{"label": _("Assigned To"), "fieldname": "assigned_to", "fieldtype": "Link", "options": "Tracora Employee", "width": 140},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "Tracora Location", "width": 130},
	]
	conditions = []
	values = {}

	add_filter_condition(conditions, values, "a.branch", "branch", filters.get("branch"))
	add_filter_condition(conditions, values, "a.holding_company", "company", filters.get("company") or filters.get("holding_company"))
	add_filter_condition(conditions, values, "a.status", "status", filters.get("status"))

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
	query = f"""
		SELECT
			a.branch,
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
	data = frappe.db.sql(query, values, as_dict=True)
	return columns, data

# -------------------------------------------------------------------------
# 4. Assets by Department (FR-37 Unassigned Stock)
# -------------------------------------------------------------------------
def get_assets_by_department(filters):
	columns = [
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 160},
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Tracora Brand", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Assigned To"), "fieldname": "assigned_to", "fieldtype": "Link", "options": "Tracora Employee", "width": 140},
	]
	conditions = []
	values = {}

	add_filter_condition(conditions, values, "a.holding_company", "company", filters.get("company") or filters.get("holding_company"))
	if filters.get("department"):
		add_filter_condition(conditions, values, "e.department", "department", filters.get("department"))

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
	query = f"""
		SELECT
			CASE
				WHEN a.assigned_to IS NULL OR a.assigned_to = '' THEN 'Unassigned Stock'
				WHEN e.department IS NULL OR e.department = '' THEN 'No Department'
				ELSE e.department
			END as department,
			a.asset_tag,
			a.asset_name,
			a.brand,
			a.status,
			a.assigned_to
		FROM `tabTracora Asset` a
		LEFT JOIN `tabTracora Employee` e ON a.assigned_to = e.name
		{where_clause}
		ORDER BY
			CASE WHEN a.assigned_to IS NULL OR a.assigned_to = '' THEN 1 ELSE 0 END ASC,
			department ASC,
			a.name ASC
	"""
	data = frappe.db.sql(query, values, as_dict=True)
	return columns, data

# -------------------------------------------------------------------------
# 5. Assets by Employee (Internal only, Exited Alert)
# -------------------------------------------------------------------------
def get_assets_by_employee(filters):
	columns = [
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
	conditions = ["c.company_type = 'Internal'"]
	values = {}

	add_filter_condition(conditions, values, "e.company", "company", filters.get("company"))
	add_filter_condition(conditions, values, "e.department", "department", filters.get("department"))
	add_filter_condition(conditions, values, "e.name", "employee", filters.get("employee"))

	where_clause = " WHERE " + " AND ".join(conditions)
	query = f"""
		SELECT
			e.name as employee,
			e.employee_name,
			e.company,
			e.department,
			a.asset_tag,
			a.asset_name,
			a.serial_no,
			a.assigned_on,
			a.status,
			e.status as employee_status
		FROM `tabTracora Asset` a
		INNER JOIN `tabTracora Employee` e ON a.assigned_to = e.name
		INNER JOIN `tabTracora Company` c ON e.company = c.name
		{where_clause}
		ORDER BY e.company ASC, e.employee_name ASC, a.name ASC
	"""
	data = frappe.db.sql(query, values, as_dict=True)
	message = _("Covers internal company employees only (FR-77). For client/partner-placed assets, see External Custody.")
	return columns, data, message

# -------------------------------------------------------------------------
# 6. External Custody (External only)
# -------------------------------------------------------------------------
def get_external_custody(filters):
	columns = [
		{"label": _("Client / Partner Company"), "fieldname": "holding_company", "fieldtype": "Link", "options": "Tracora Company", "width": 180},
		{"label": _("Contact / Holder"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{"label": _("Asset Tag"), "fieldname": "asset_tag", "fieldtype": "Data", "width": 130},
		{"label": _("Asset Name"), "fieldname": "asset_name", "fieldtype": "Data", "width": 180},
		{"label": _("Serial No"), "fieldname": "serial_no", "fieldtype": "Data", "width": 120},
		{"label": _("Assigned Date"), "fieldname": "assigned_on", "fieldtype": "Date", "width": 110},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "Tracora Location", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
	]
	conditions = ["c.company_type = 'External'"]
	values = {}

	add_filter_condition(conditions, values, "a.holding_company", "holding_company", filters.get("holding_company") or filters.get("company"))
	add_filter_condition(conditions, values, "e.name", "employee", filters.get("employee"))

	where_clause = " WHERE " + " AND ".join(conditions)
	query = f"""
		SELECT
			a.holding_company,
			COALESCE(e.employee_name, a.assigned_to, 'Unassigned') as employee_name,
			a.asset_tag,
			a.asset_name,
			a.serial_no,
			a.assigned_on,
			a.location,
			a.status
		FROM `tabTracora Asset` a
		INNER JOIN `tabTracora Company` c ON a.holding_company = c.name
		LEFT JOIN `tabTracora Employee` e ON a.assigned_to = e.name
		{where_clause}
		ORDER BY a.holding_company ASC, a.name ASC
	"""
	data = frappe.db.sql(query, values, as_dict=True)
	message = _("Covers assets physically placed with external clients and partner personnel (FR-77).")
	return columns, data, message

# -------------------------------------------------------------------------
# 7. Licence Expiry (Active seats = Active + Flagged)
# -------------------------------------------------------------------------
def get_licence_expiry(filters):
	columns = [
		{"label": _("Software Name"), "fieldname": "software_name", "fieldtype": "Data", "width": 180},
		{"label": _("Licence Name"), "fieldname": "licence_name", "fieldtype": "Link", "options": "Tracora Software Licence", "width": 180},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Tracora Company", "width": 150},
		{"label": _("Licence Type"), "fieldname": "licence_type", "fieldtype": "Data", "width": 120},
		{"label": _("Licence Expiry"), "fieldname": "licence_expiry_date", "fieldtype": "Date", "width": 120},
		{"label": _("Days Remaining"), "fieldname": "days_remaining", "fieldtype": "Int", "width": 130},
		{"label": _("Active Seats"), "fieldname": "active_seats", "fieldtype": "Int", "width": 110},
		{"label": _("Status"), "fieldname": "licence_status", "fieldtype": "Data", "width": 120},
	]
	conditions = []
	values = {}

	add_filter_condition(conditions, values, "l.company", "company", filters.get("company"))
	if filters.get("licence_type") and filters.get("licence_type") != "All":
		conditions.append("l.licence_type = %(licence_type)s")
		values["licence_type"] = filters["licence_type"]
	if filters.get("licence_status"):
		add_filter_condition(conditions, values, "l.licence_status", "licence_status", filters.get("licence_status"))

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
	query = f"""
		SELECT
			l.software_name,
			l.name as licence_name,
			l.company,
			l.licence_type,
			l.licence_expiry_date,
			l.licence_status,
			(SELECT COUNT(s.name) FROM `tabTracora Licence Seat` s
			 WHERE s.parent = l.name AND s.seat_status IN ('Active', 'Flagged')) as active_seats
		FROM `tabTracora Software Licence` l
		{where_clause}
		ORDER BY
			CASE WHEN l.licence_expiry_date IS NULL THEN 1 ELSE 0 END ASC,
			l.licence_expiry_date ASC,
			l.name ASC
	"""
	raw_data = frappe.db.sql(query, values, as_dict=True)
	ref_today = getdate(today())
	data = []
	for row in raw_data:
		if row.get("licence_expiry_date"):
			exp_date = getdate(row["licence_expiry_date"])
			row["days_remaining"] = date_diff(exp_date, ref_today)
		else:
			row["days_remaining"] = None
		data.append(row)

	return columns, data

# -------------------------------------------------------------------------
# 8. Licence Renewal Due (next_renewal_date ASC)
# -------------------------------------------------------------------------
def get_licence_renewal_due(filters):
	columns = [
		{"label": _("Software Name"), "fieldname": "software_name", "fieldtype": "Data", "width": 180},
		{"label": _("Licence Name"), "fieldname": "licence_name", "fieldtype": "Link", "options": "Tracora Software Licence", "width": 180},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Tracora Company", "width": 150},
		{"label": _("Renewal Cycle"), "fieldname": "renewal_cycle", "fieldtype": "Data", "width": 130},
		{"label": _("Next Renewal Due"), "fieldname": "next_renewal_date", "fieldtype": "Date", "width": 140},
		{"label": _("Days Until Renewal"), "fieldname": "days_until_renewal", "fieldtype": "Int", "width": 150},
		{"label": _("Status"), "fieldname": "licence_status", "fieldtype": "Data", "width": 120},
	]
	conditions = []
	values = {}

	add_filter_condition(conditions, values, "l.company", "company", filters.get("company"))
	if filters.get("renewal_cycle") and filters.get("renewal_cycle") != "All":
		conditions.append("l.renewal_cycle = %(renewal_cycle)s")
		values["renewal_cycle"] = filters["renewal_cycle"]

	include_nulls = frappe.utils.cint(filters.get("include_non_renewing"))
	if not include_nulls:
		conditions.append("l.next_renewal_date IS NOT NULL")

	where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
	query = f"""
		SELECT
			l.software_name,
			l.name as licence_name,
			l.company,
			l.renewal_cycle,
			l.next_renewal_date,
			l.licence_status
		FROM `tabTracora Software Licence` l
		{where_clause}
		ORDER BY
			CASE WHEN l.next_renewal_date IS NULL THEN 1 ELSE 0 END ASC,
			l.next_renewal_date ASC,
			l.name ASC
	"""
	raw_data = frappe.db.sql(query, values, as_dict=True)
	ref_today = getdate(today())
	data = []
	for row in raw_data:
		if row.get("next_renewal_date"):
			r_date = getdate(row["next_renewal_date"])
			row["days_until_renewal"] = date_diff(r_date, ref_today)
		else:
			row["days_until_renewal"] = None
		data.append(row)

	return columns, data
