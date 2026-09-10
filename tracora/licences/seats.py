# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_installed_licences(asset: str):
	"""Returns installed software licences/seats for a device asset.
	Requires read permission on both the Tracora Asset and Tracora Software Licence doctype.
	"""
	if not asset or not frappe.db.exists("Tracora Asset", asset):
		return []

	if not frappe.has_permission("Tracora Asset", "read", doc=asset):
		frappe.throw(_("Not permitted to view Asset {0}").format(asset), frappe.PermissionError)

	if not frappe.has_permission("Tracora Software Licence", "read"):
		frappe.throw(_("Not permitted to view Software Licences"), frappe.PermissionError)

	seats = frappe.get_all(
		"Tracora Licence Seat",
		filters={"device": asset},
		fields=["name", "parent", "device", "user", "seat_status", "flagged_reason"],
		order_by="creation desc",
		limit=50,
	)

	allowed_seats = []
	for s in seats:
		if frappe.has_permission("Tracora Software Licence", "read", doc=s.parent):
			allowed_seats.append(s)

	return allowed_seats
