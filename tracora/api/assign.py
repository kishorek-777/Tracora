# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from tracora.licences.flagging import flag_active_seats_for_device


def _execute_asset_assignment(asset_name, employee_name, assignment_date=None, reference=None, remarks=None):
	asset_doc = frappe.get_doc("Tracora Asset", asset_name)

	# FR-93: Refuse upfront if shared equipment
	if asset_doc.is_shared:
		frappe.throw(
			_("Asset '{0}' is marked as shared equipment and cannot be assigned to an individual (FR-93). Uncheck 'Is Shared' on the asset if transferring to personal custody.").format(
				asset_doc.asset_tag or asset_doc.name
			),
			frappe.ValidationError
		)

	# FR-58: Refuse if Under Maintenance, Lost, or Retired
	if asset_doc.status in ("Under Maintenance", "Lost", "Retired"):
		frappe.throw(
			_("Asset '{0}' has status '{1}' and cannot be assigned (FR-58). Assets must be In Store or Recovered before assignment.").format(
				asset_doc.asset_tag or asset_doc.name, asset_doc.status
			),
			frappe.ValidationError
		)

	# FR-57: Refuse if already assigned, naming current holder
	if asset_doc.assigned_to:
		holder_name = frappe.db.get_value("Tracora Employee", asset_doc.assigned_to, "employee_name") or asset_doc.assigned_to
		frappe.throw(
			_("Asset '{0}' is already assigned to {1} ({2}) (FR-57). Please unassign the asset before reassigning.").format(
				asset_doc.asset_tag or asset_doc.name, holder_name, asset_doc.assigned_to
			),
			frappe.ValidationError
		)

	emp_doc = frappe.get_doc("Tracora Employee", employee_name)

	from_employee = asset_doc.assigned_to
	from_status = asset_doc.status
	from_location = asset_doc.location
	from_company = asset_doc.holding_company

	frappe.flags.in_tracora_assign = True
	asset_doc.assigned_to = emp_doc.name
	asset_doc.assigned_on = assignment_date or frappe.utils.today()
	asset_doc.status = "Assigned"
	asset_doc.holding_company = emp_doc.company
	if emp_doc.branch:
		asset_doc.branch = emp_doc.branch
	asset_doc.save()
	frappe.flags.in_tracora_assign = False

	movement = frappe.get_doc({
		"doctype": "Tracora Asset Movement",
		"asset": asset_doc.name,
		"movement_type": "Assign",
		"movement_date": frappe.utils.now_datetime(),
		"from_employee": from_employee,
		"to_employee": emp_doc.name,
		"from_company": from_company,
		"to_company": emp_doc.company,
		"from_location": from_location,
		"to_location": asset_doc.location,
		"from_status": from_status,
		"to_status": "Assigned",
		"remarks": (remarks or reference or "").strip(),
		"recorded_by": frappe.session.user
	})
	movement.insert()

	return {"asset": asset_doc.name, "movement": movement.name}


@frappe.whitelist()
def assign_asset(asset, employee, reference=None, assignment_date=None, remarks=None):
	if not employee or not frappe.db.exists("Tracora Employee", employee):
		frappe.throw(_("Employee '{0}' does not exist.").format(employee), frappe.DoesNotExistError)

	emp_status = frappe.db.get_value("Tracora Employee", employee, "status")
	if emp_status in ("Exited", "Pending Clearance"):
		frappe.throw(
			_("Cannot assign asset to employee '{0}' because employee status is '{1}' (FR-69).").format(
				employee, emp_status
			),
			frappe.ValidationError
		)

	return _execute_asset_assignment(asset, employee, assignment_date, reference, remarks)


@frappe.whitelist()
def assign_to_employee(employee, assets, reference=None, assignment_date=None, remarks=None):
	if isinstance(assets, str):
		try:
			assets = json.loads(assets)
		except Exception:
			assets = [a.strip() for a in assets.split(",") if a.strip()]

	if not assets:
		frappe.throw(_("Please select at least one asset to assign."), frappe.ValidationError)

	if not employee or not frappe.db.exists("Tracora Employee", employee):
		frappe.throw(_("Employee '{0}' does not exist.").format(employee), frappe.DoesNotExistError)

	emp_status = frappe.db.get_value("Tracora Employee", employee, "status")
	if emp_status in ("Exited", "Pending Clearance"):
		frappe.throw(
			_("Cannot assign asset to employee '{0}' because employee status is '{1}' (FR-69).").format(
				employee, emp_status
			),
			frappe.ValidationError
		)

	# Atomic transaction: roll back everything if any asset assignment fails
	results = []
	try:
		for asset_name in assets:
			res = _execute_asset_assignment(asset_name, employee, assignment_date, reference, remarks)
			results.append(res)
	except Exception:
		frappe.db.rollback()
		raise

	return {"assigned_count": len(results), "items": results}


@frappe.whitelist()
def unassign_asset(asset, location, remarks, condition=None, status=None):
	if not remarks or not str(remarks).strip():
		frappe.throw(_("Remarks are mandatory when unassigning an asset (FR-51)."), frappe.ValidationError)

	if not location or not frappe.db.exists("Tracora Location", location):
		frappe.throw(_("Return location is mandatory and must be a valid Location (FR-52)."), frappe.ValidationError)

	asset_doc = frappe.get_doc("Tracora Asset", asset)
	if not asset_doc.assigned_to:
		frappe.throw(
			_("Asset '{0}' is not currently assigned.").format(asset_doc.asset_tag or asset_doc.name),
			frappe.ValidationError
		)

	previous_holder = asset_doc.assigned_to
	previous_status = asset_doc.status
	previous_location = asset_doc.location

	target_status = status or "In Store"
	target_condition = condition or asset_doc.condition

	frappe.flags.in_tracora_assign = True
	asset_doc.assigned_to = None
	asset_doc.assigned_on = None
	asset_doc.location = location
	asset_doc.status = target_status
	asset_doc.condition = target_condition
	asset_doc.save()
	frappe.flags.in_tracora_assign = False

	movement = frappe.get_doc({
		"doctype": "Tracora Asset Movement",
		"asset": asset_doc.name,
		"movement_type": "Unassign",
		"movement_date": frappe.utils.now_datetime(),
		"from_employee": previous_holder,
		"to_employee": None,
		"from_location": previous_location,
		"to_location": location,
		"from_status": previous_status,
		"to_status": target_status,
		"remarks": str(remarks).strip(),
		"recorded_by": frappe.session.user
	})
	movement.insert()

	# FR-59: Flag active licence seats installed on this device
	flag_active_seats_for_device(asset_doc.name, _("Device '{0}' was unassigned").format(asset_doc.asset_tag or asset_doc.name))

	# FR-69: Pending Clearance clears to Exited automatically on last release (checking both assets and software seats)
	emp_status = frappe.db.get_value("Tracora Employee", previous_holder, "status")
	if emp_status == "Pending Clearance":
		remaining_assets = frappe.db.count("Tracora Asset", {"assigned_to": previous_holder})
		remaining_seats = 0
		if frappe.db.exists("DocType", "Tracora Licence Seat"):
			remaining_seats = frappe.db.count(
				"Tracora Licence Seat",
				{"user": previous_holder, "seat_status": ["in", ["Active", "Flagged"]]}
			)
		if remaining_assets == 0 and remaining_seats == 0:
			frappe.db.set_value("Tracora Employee", previous_holder, "status", "Exited")

	return {"asset": asset_doc.name, "movement": movement.name, "status": target_status}


@frappe.whitelist()
def transfer_ownership(asset, to_owner, reason):
	if not to_owner or not frappe.db.exists("Tracora Company", to_owner):
		frappe.throw(_("Destination owner company '{0}' does not exist.").format(to_owner), frappe.ValidationError)

	if not reason or not str(reason).strip():
		frappe.throw(_("Reason is mandatory when transferring ownership (FR-82)."), frappe.ValidationError)

	asset_doc = frappe.get_doc("Tracora Asset", asset)
	if asset_doc.owner_company == to_owner:
		frappe.throw(
			_("Asset '{0}' is already owned by '{1}'.").format(asset_doc.asset_tag or asset_doc.name, to_owner),
			frappe.ValidationError
		)

	from_owner = asset_doc.owner_company
	frappe.flags.in_tracora_transfer = True
	asset_doc.owner_company = to_owner
	asset_doc.save()
	frappe.flags.in_tracora_transfer = False

	movement = frappe.get_doc({
		"doctype": "Tracora Asset Movement",
		"asset": asset_doc.name,
		"movement_type": "Ownership Transfer",
		"movement_date": frappe.utils.now_datetime(),
		"from_owner": from_owner,
		"to_owner": to_owner,
		"from_location": asset_doc.location,
		"to_location": asset_doc.location,
		"from_status": asset_doc.status,
		"to_status": asset_doc.status,
		"remarks": str(reason).strip(),
		"recorded_by": frappe.session.user
	})
	movement.insert()

	return {"asset": asset_doc.name, "from_owner": from_owner, "to_owner": to_owner, "movement": movement.name}


@frappe.whitelist()
def recover_asset(asset, remarks, condition=None):
	if not remarks or not str(remarks).strip():
		frappe.throw(_("Remarks are mandatory when recovering an asset (FR-84)."), frappe.ValidationError)

	asset_doc = frappe.get_doc("Tracora Asset", asset)
	if asset_doc.status != "Lost":
		frappe.throw(
			_("Asset '{0}' cannot be recovered because its status is '{1}', not 'Lost' (FR-84).").format(
				asset_doc.asset_tag or asset_doc.name, asset_doc.status
			),
			frappe.ValidationError
		)

	from_status = asset_doc.status
	asset_doc.status = "Recovered"
	if condition:
		asset_doc.condition = condition
	asset_doc.save()

	movement = frappe.get_doc({
		"doctype": "Tracora Asset Movement",
		"asset": asset_doc.name,
		"movement_type": "Recovered",
		"movement_date": frappe.utils.now_datetime(),
		"from_status": from_status,
		"to_status": "Recovered",
		"from_location": asset_doc.location,
		"to_location": asset_doc.location,
		"remarks": str(remarks).strip(),
		"recorded_by": frappe.session.user
	})
	movement.insert()

	return {"asset": asset_doc.name, "status": "Recovered", "movement": movement.name}


@frappe.whitelist()
def get_movement_history(asset):
	movements = frappe.db.get_all(
		"Tracora Asset Movement",
		filters={"asset": asset},
		fields=[
			"name",
			"movement_type",
			"movement_date",
			"recorded_by",
			"from_employee",
			"to_employee",
			"from_company",
			"to_company",
			"from_owner",
			"to_owner",
			"from_location",
			"to_location",
			"from_status",
			"to_status",
			"remarks",
			"creation"
		],
		order_by="movement_date desc, creation desc"
	)

	for m in movements:
		user_fullname = frappe.utils.get_fullname(m.recorded_by) if m.recorded_by else ""
		m["by_user"] = user_fullname or m.recorded_by or "System"

		m_type = m.movement_type
		date_str = frappe.utils.format_datetime(m.movement_date, "dd MMM yyyy HH:mm") if m.movement_date else ""

		if m_type == "Assign":
			emp_name = frappe.db.get_value("Tracora Employee", m.to_employee, "employee_name") or m.to_employee
			sentence = f"Assigned to {emp_name} ({m.to_employee}) — {date_str} — by {m['by_user']}"
		elif m_type == "Unassign":
			prev_emp = frappe.db.get_value("Tracora Employee", m.from_employee, "employee_name") or m.from_employee or "previous holder"
			sentence = f"Unassigned from {prev_emp} to location {m.to_location or 'Store'} — {date_str} — by {m['by_user']}"
		elif m_type == "Ownership Transfer":
			sentence = f"Ownership transferred from {m.from_owner} to {m.to_owner} — {date_str} — by {m['by_user']}"
		elif m_type == "Recovered":
			sentence = f"Recovered from Lost status — {date_str} — by {m['by_user']}"
		elif m_type == "Exit Release":
			sentence = f"Released at employee exit from {m.from_employee} — {date_str} — by {m['by_user']}"
		elif m_type == "Maintenance Sent":
			sentence = f"Sent to maintenance — {date_str} — by {m['by_user']}"
		elif m_type == "Maintenance Returned":
			sentence = f"Returned from maintenance — {date_str} — by {m['by_user']}"
		elif m_type == "Location Change":
			sentence = f"Location changed from {m.from_location} to {m.to_location} — {date_str} — by {m['by_user']}"
		elif m_type == "Label Reprint":
			sentence = f"Label reprinted — {date_str} — by {m['by_user']}"
		else:
			sentence = f"{m_type} — {date_str} — by {m['by_user']}"

		m["sentence"] = sentence

	return movements


@frappe.whitelist()
def get_employee_held_assets(employee):
	return frappe.db.get_all(
		"Tracora Asset",
		filters={"assigned_to": employee},
		fields=[
			"name",
			"asset_tag",
			"asset_name",
			"brand",
			"model_number",
			"serial_no",
			"assigned_on",
			"location",
			"status",
			"condition"
		],
		order_by="assigned_on desc"
	)
