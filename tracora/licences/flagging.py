# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe


def flag_active_seats_for_device(asset_name: str, reason: str = "") -> list:
	"""
	Releases all active licence seats installed on asset_name when unassigned or retired.
	Groups matching seats by parent licence and saves each parent exactly once,
	preventing double-save races and TimestampMismatchError.
	"""
	if not frappe.db.exists("DocType", "Tracora Licence Seat"):
		return []

	seats = frappe.db.get_all(
		"Tracora Licence Seat",
		filters={"device": asset_name, "seat_status": "Active"},
		fields=["name", "parent", "user", "device"]
	)
	if not seats:
		return []

	# Group by parent licence
	seats_by_parent = defaultdict(list)
	for s in seats:
		seats_by_parent[s.parent].append(s)

	released_summary = []
	for parent_name, seat_list in seats_by_parent.items():
		licence_doc = frappe.get_doc("Tracora Software Licence", parent_name)
		target_seat_names = {s.name for s in seat_list}
		for seat_row in licence_doc.seats:
			if seat_row.name in target_seat_names:
				seat_row.seat_status = "Released"
				released_summary.append({
					"licence": parent_name,
					"seat": seat_row.name,
					"device": asset_name,
					"user": seat_row.user,
					"status": "Released"
				})
		licence_doc.save(ignore_permissions=True)

	return released_summary


release_active_seats_for_device = flag_active_seats_for_device
