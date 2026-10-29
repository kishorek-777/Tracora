# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, today
from tracora.api.lookup import _has_tracora_access

VALID_CONDITIONS = ("New", "Good", "Fair", "Poor", "Not Working")
VALID_STATUSES = ("Verified", "Discrepancy", "Missing")


@frappe.whitelist(methods=["POST"])
def submit_asset_audit(
	asset: str,
	audit_status: str = "Verified",
	remarks: str = "",
	condition: str | None = None,
	location: str | None = None,
) -> dict:
	"""
	API endpoint for Mobile PWA and Desk to submit an asset audit.
	Accessible to Tracora Auditor, Tracora Admin, and Tracora Super Admin.
	Creates an immutable Tracora Asset Audit Log entry and updates Tracora Asset summary fields.
	"""
	if not _has_tracora_access(frappe.session.user):
		frappe.throw(
			_("Access denied: Tracora Auditor, Admin, or Super Admin role required"),
			frappe.PermissionError,
		)

	if not asset or not frappe.db.exists("Tracora Asset", asset):
		frappe.throw(_("Asset '{0}' does not exist.").format(asset), frappe.DoesNotExistError)

	audit_status = (audit_status or "Verified").strip()
	if audit_status not in VALID_STATUSES:
		frappe.throw(
			_("Audit Status must be one of: {0}").format(", ".join(VALID_STATUSES)),
			frappe.ValidationError,
		)

	clean_remarks = (remarks or "").strip()
	if not clean_remarks:
		frappe.throw(_("Audit remarks are mandatory."), frappe.ValidationError)

	if condition and condition not in VALID_CONDITIONS:
		frappe.throw(
			_("Condition must be one of: {0}").format(", ".join(VALID_CONDITIONS)),
			frappe.ValidationError,
		)

	audit_date = today()
	auditor_user = frappe.session.user
	auditor_name = frappe.utils.get_fullname(auditor_user) or auditor_user

	# 1. Insert immutable Audit Log
	audit_log = frappe.get_doc({
		"doctype": "Tracora Asset Audit Log",
		"asset": asset,
		"audit_date": audit_date,
		"auditor": auditor_user,
		"auditor_name": auditor_name,
		"audit_status": audit_status,
		"remarks": clean_remarks,
		"location": location,
		"condition": condition,
	})
	audit_log.insert()

	# 2. Update Tracora Asset audit summary fields
	asset_doc = frappe.get_doc("Tracora Asset", asset)
	asset_doc.audit_date = audit_date
	status_prefix = f"[{audit_status}] " if not clean_remarks.startswith("[") else ""
	asset_doc.audit_remarks = f"{status_prefix}{clean_remarks}"

	if condition and asset_doc.condition != condition:
		asset_doc.condition = condition

	asset_doc.flags.ignore_permissions = True
	asset_doc.save()

	return {
		"success": True,
		"audit_log": audit_log.name,
		"asset": asset,
		"audit_date": audit_date,
		"audit_status": audit_status,
		"remarks": clean_remarks,
		"auditor": auditor_name,
	}


@frappe.whitelist(methods=["GET", "POST"])
def get_asset_audit_history(asset: str) -> list[dict]:
	"""
	Returns chronological audit log records for the specified asset.
	"""
	if not _has_tracora_access(frappe.session.user):
		frappe.throw(_("Access denied: Tracora role required"), frappe.PermissionError)

	if not asset:
		return []

	return frappe.get_all(
		"Tracora Asset Audit Log",
		filters={"asset": asset},
		fields=[
			"name",
			"audit_date",
			"auditor",
			"auditor_name",
			"audit_status",
			"remarks",
			"condition",
			"location",
			"creation",
		],
		order_by="audit_date desc, creation desc",
		limit=50,
	)
