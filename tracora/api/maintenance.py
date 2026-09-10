# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, format_date


@frappe.whitelist()
def send_to_maintenance(asset, vendor, reason, date_sent=None, due_date=None):
	"""
	P6 / FR-18: Opens a maintenance log, transitions asset to 'Under Maintenance',
	and records an immutable 'Maintenance Sent' movement in the same transaction.
	"""
	if not asset or not vendor or not reason:
		frappe.throw(_("Asset, Vendor, and Reason are mandatory to send an asset to maintenance."), frappe.ValidationError)

	asset_doc = frappe.get_doc("Tracora Asset", asset)

	if asset_doc.status in ("Under Maintenance", "Lost", "Retired"):
		frappe.throw(
			_("Asset '{0}' has status '{1}' and cannot be sent to maintenance.").format(
				asset_doc.asset_tag or asset_doc.name, asset_doc.status
			),
			frappe.ValidationError
		)

	# Store pre-maintenance status so return restores it exactly
	pre_status = asset_doc.status
	date_sent = date_sent or today()

	# Create Maintenance Log using .insert() so DocType validate() rules execute
	log = frappe.get_doc({
		"doctype": "Tracora Maintenance Log",
		"asset": asset_doc.name,
		"vendor": vendor.strip(),
		"reason": reason.strip(),
		"date_sent": date_sent,
		"due_date": due_date,
		"pre_maintenance_status": pre_status,
		"log_status": "Open",
		"recorded_by": frappe.session.user,
	})
	log.insert()

	# Update Asset status atomically
	asset_doc.status = "Under Maintenance"
	asset_doc.flags.ignore_permissions = True
	asset_doc.save()

	# Emit immutable audit movement
	holding_company = asset_doc.holding_company or asset_doc.owner_company
	movement = frappe.get_doc({
		"doctype": "Tracora Asset Movement",
		"asset": asset_doc.name,
		"movement_type": "Maintenance Sent",
		"from_employee": asset_doc.assigned_to,
		"to_employee": asset_doc.assigned_to,
		"from_company": holding_company,
		"to_company": holding_company,
		"from_owner": asset_doc.owner_company,
		"to_owner": asset_doc.owner_company,
		"from_location": asset_doc.location,
		"to_location": asset_doc.location,
		"from_status": pre_status,
		"to_status": "Under Maintenance",
		"remarks": _("Sent to maintenance at {0}. Reason: {1}").format(vendor, reason),
		"recorded_by": frappe.session.user,
	})
	movement.flags.ignore_permissions = True
	movement.insert()

	return {
		"maintenance_log": log.name,
		"asset": asset_doc.name,
		"status": asset_doc.status,
	}


@frappe.whitelist()
def close_maintenance(log_name, condition_on_return=None, date_returned=None, is_beyond_repair=False, remarks=None):
	"""
	P6 / FR-18: Closes maintenance log.
	- If is_beyond_repair: Asset status -> Retired, holder cleared and explicitly attributed in movement.
	- Else: Restores asset to pre_maintenance_status, updates condition, and writes 'Maintenance Returned' movement.
	"""
	if not log_name:
		frappe.throw(_("Maintenance log name is required."), frappe.ValidationError)

	log = frappe.get_doc("Tracora Maintenance Log", log_name)

	# Idempotency / state guard
	if log.log_status != "Open":
		frappe.throw(
			_("Maintenance log '{0}' has already been closed as '{1}' and cannot be closed again.").format(
				log.name, log.log_status
			),
			frappe.ValidationError
		)

	asset_doc = frappe.get_doc("Tracora Asset", log.asset)
	date_returned = date_returned or today()
	is_beyond_repair = frappe.parse_json(is_beyond_repair) if isinstance(is_beyond_repair, str) else bool(is_beyond_repair)

	if is_beyond_repair:
		# Terminal Beyond Repair closure
		log.log_status = "Beyond Repair"
		log.date_returned = date_returned
		log.condition_on_return = condition_on_return or "Not Working"
		log.remarks = remarks or _("Declared beyond repair.")
		log.save()

		current_holder = asset_doc.assigned_to

		# Clear holder and retire asset
		asset_doc.status = "Retired"
		asset_doc.condition = log.condition_on_return
		frappe.flags.in_tracora_assign = True
		try:
			asset_doc.assigned_to = None
			asset_doc.assigned_on = None
			asset_doc.flags.ignore_permissions = True
			asset_doc.save()
		finally:
			frappe.flags.in_tracora_assign = False

		# Explicitly document the holder clearing in the Beyond Repair movement row
		holding_company = asset_doc.holding_company or asset_doc.owner_company
		movement = frappe.get_doc({
			"doctype": "Tracora Asset Movement",
			"asset": asset_doc.name,
			"movement_type": "Beyond Repair",
			"from_employee": current_holder,
			"to_employee": None,
			"from_company": holding_company,
			"to_company": holding_company,
			"from_owner": asset_doc.owner_company,
			"to_owner": asset_doc.owner_company,
			"from_location": asset_doc.location,
			"to_location": asset_doc.location,
			"from_status": "Under Maintenance",
			"to_status": "Retired",
			"remarks": remarks or _("Declared beyond repair at {0}. Custody cleared and asset retired.").format(log.vendor),
			"recorded_by": frappe.session.user,
		})
		movement.flags.ignore_permissions = True
		movement.insert()

	else:
		# Normal closure returning to service
		if not condition_on_return:
			frappe.throw(_("Condition on return is required when closing maintenance (FR-18)."), frappe.ValidationError)

		log.log_status = "Closed"
		log.date_returned = date_returned
		log.condition_on_return = condition_on_return
		if remarks:
			log.remarks = remarks
		log.save()

		# Restore pre-maintenance status
		asset_doc.status = log.pre_maintenance_status or "In Store"
		asset_doc.condition = condition_on_return
		asset_doc.flags.ignore_permissions = True
		asset_doc.save()

		# Emit Maintenance Returned movement
		holding_company = asset_doc.holding_company or asset_doc.owner_company
		movement = frappe.get_doc({
			"doctype": "Tracora Asset Movement",
			"asset": asset_doc.name,
			"movement_type": "Maintenance Returned",
			"from_employee": asset_doc.assigned_to,
			"to_employee": asset_doc.assigned_to,
			"from_company": holding_company,
			"to_company": holding_company,
			"from_owner": asset_doc.owner_company,
			"to_owner": asset_doc.owner_company,
			"from_location": asset_doc.location,
			"to_location": asset_doc.location,
			"from_status": "Under Maintenance",
			"to_status": asset_doc.status,
			"remarks": remarks or _("Returned from {0} in {1} condition.").format(log.vendor, condition_on_return),
			"recorded_by": frappe.session.user,
		})
		movement.flags.ignore_permissions = True
		movement.insert()

	return {
		"maintenance_log": log.name,
		"asset": asset_doc.name,
		"status": asset_doc.status,
		"condition": asset_doc.condition,
		"log_status": log.log_status,
	}


@frappe.whitelist()
def get_open_maintenance(asset):
	"""
	Returns active open maintenance details for the asset banner.
	"""
	if not asset:
		return None

	return frappe.db.get_value(
		"Tracora Maintenance Log",
		{"asset": asset, "log_status": "Open"},
		["name", "vendor", "date_sent", "due_date", "reason"],
		as_dict=True
	)