import frappe
from frappe import _


@frappe.whitelist(methods=["GET", "POST"])
def find_asset(q: str | None = None) -> dict:
	"""
	PWA asset lookup endpoint supporting exact asset_tag, exact serial_no,
	and partial asset_name search (FR-31 to FR-35, FR-91).

	Returns a structured payload containing top-level `match_type` set to
	one of: "single", "multiple", "none".

	Permission boundary note:
	Row-level permission checks (asset_doc.check_permission / holder.check_permission)
	are intentionally omitted here because Tracora's role model grants Admin and
	Super Admin global read access to Assets and Employees across all 9 companies
	without row-level company or branch partitions. Session authentication is enforced
	below so unauthenticated Guest calls are rejected (FR-35).
	"""
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	query = (q or "").strip()
	if not query:
		return {
			"match_type": "none",
			"query": "",
			"message": _("Search query is empty"),
		}

	# 1. Exact asset_tag match
	exact_asset = frappe.db.get_value(
		"Tracora Asset",
		{"asset_tag": query},
		"name",
	)

	# 2. Exact serial_no match (if not matched by tag)
	if not exact_asset:
		exact_asset = frappe.db.get_value(
			"Tracora Asset",
			{"serial_no": query},
			"name",
		)

	# 3. Exact match short-circuit:
	# If an exact asset_tag or serial_no match is found, return it immediately as
	# a single match. Do NOT run the partial asset_name search in that case.
	if exact_asset:
		return _build_single_match_payload(exact_asset, query)

	# 4. Partial asset_name search (capped at 20 rows, FR-91)
	name_matches = frappe.get_list(
		"Tracora Asset",
		filters={"asset_name": ["like", f"%{query}%"]},
		fields=[
			"name",
			"asset_tag",
			"asset_name",
			"brand",
			"model_number",
			"serial_no",
			"status",
			"condition",
			"assigned_to",
			"location",
			"holding_company",
		],
		order_by="creation desc",
		limit=20,
	)

	if name_matches:
		# Attach holder display name for multi-match list to aid human disambiguation
		for row in name_matches:
			if row.get("assigned_to"):
				row["holder_name"] = frappe.db.get_value(
					"Tracora Employee",
					row["assigned_to"],
					"employee_name",
				)
			else:
				row["holder_name"] = None

		return {
			"match_type": "multiple",
			"query": query,
			"count": len(name_matches),
			"results": name_matches,
		}

	# 5. No match found (FR-34: names searched query, creates zero records)
	return {
		"match_type": "none",
		"query": query,
		"message": _("No asset found matching '{0}'").format(query),
	}


def _build_single_match_payload(asset_name: str, query: str) -> dict:
	asset_doc = frappe.get_doc("Tracora Asset", asset_name)

	# Explicit field list for asset ? never SELECT *
	asset_payload = {
		"name": asset_doc.name,
		"asset_tag": asset_doc.asset_tag,
		"asset_name": asset_doc.asset_name,
		"brand": asset_doc.brand,
		"model_number": asset_doc.model_number,
		"serial_no": asset_doc.serial_no,
		"owner_company": asset_doc.owner_company,
		"holding_company": asset_doc.holding_company,
		"branch": asset_doc.branch,
		"location": asset_doc.location,
		"is_shared": getattr(asset_doc, "is_shared", 0),
		"point_of_contact": asset_doc.point_of_contact,
		"assigned_to": asset_doc.assigned_to,
		"assigned_on": str(asset_doc.assigned_on) if asset_doc.assigned_on else None,
		"status": asset_doc.status,
		"condition": asset_doc.condition,
		"label_printed_on": str(asset_doc.label_printed_on)
		if getattr(asset_doc, "label_printed_on", None)
		else None,
	}

	# Holder details ? explicit projection.
	# Strictly omits mobile, email, aadhaar_number, and permanent_address.
	holder_payload = None
	if asset_doc.assigned_to:
		holder_doc = frappe.get_doc("Tracora Employee", asset_doc.assigned_to)
		holder_payload = {
			"employee_code": holder_doc.employee_code or holder_doc.name,
			"employee_name": holder_doc.employee_name,
			"company": holder_doc.company,
			"company_type": holder_doc.company_type,
		}
		if holder_doc.company_type == "External":
			holder_payload["designation"] = holder_doc.designation
		else:
			holder_payload["branch"] = holder_doc.branch
			holder_payload["department"] = holder_doc.department

	# Open maintenance record (if any)
	open_maint = frappe.get_list(
		"Tracora Maintenance Log",
		filters={"asset": asset_doc.name, "log_status": "Open"},
		fields=[
			"name",
			"vendor",
			"date_sent",
			"due_date",
			"log_status",
			"pre_maintenance_status",
			"reason",
			"remarks",
		],
		limit=1,
	)
	open_maintenance = open_maint[0] if open_maint else None

	# Active licence seats on this asset device
	licence_seats = frappe.db.sql(
		"""
		SELECT
			s.name,
			s.parent,
			s.user,
			s.seat_status,
			s.software_key,
			l.software_name,
			l.licence_name,
			l.licence_type
		FROM `tabTracora Licence Seat` s
		JOIN `tabTracora Software Licence` l ON s.parent = l.name
		WHERE s.device = %(device)s
		  AND s.seat_status = 'Active'
		ORDER BY s.creation DESC
		""",
		{"device": asset_doc.name},
		as_dict=True,
	)

	# Last 20 movements
	recent_movements = frappe.get_list(
		"Tracora Asset Movement",
		filters={"asset": asset_doc.name},
		fields=[
			"name",
			"movement_type",
			"movement_date",
			"from_employee",
			"to_employee",
			"from_company",
			"to_company",
			"from_location",
			"to_location",
			"from_status",
			"to_status",
			"remarks",
			"recorded_by",
		],
		order_by="movement_date desc, creation desc",
		limit=20,
	)

	return {
		"match_type": "single",
		"query": query,
		"asset": asset_payload,
		"holder": holder_payload,
		"open_maintenance": open_maintenance,
		"licence_seats": licence_seats,
		"recent_movements": recent_movements,
	}


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def get_session_info() -> dict:
	"""
	Returns active session user and valid CSRF token.
	Used by Tracora Mobile PWA after login or on demand to refresh CSRF token.
	Returns user as None for unauthenticated (Guest) sessions.
	"""
	return {
		"user": frappe.session.user if frappe.session.user != "Guest" else None,
		"csrf_token": frappe.sessions.get_csrf_token(),
	}
