# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe

RECORD_TYPES = [
	{"type_name": "Device", "icon": "server", "sort_order": 10},
	{"type_name": "Building", "icon": "building", "sort_order": 20},
	{"type_name": "Vendor", "icon": "store", "sort_order": 30},
	{"type_name": "Other", "icon": "layers", "sort_order": 99},
]


def execute():
	for rt in RECORD_TYPES:
		name = rt["type_name"]
		# Idempotent: Never update an existing one
		if frappe.db.exists("Tracora Infra Record Type", name) or frappe.db.exists(
			"Tracora Infra Record Type", {"type_name": name}
		):
			continue

		doc = frappe.new_doc("Tracora Infra Record Type")
		doc.type_name = name
		doc.icon = rt.get("icon")
		doc.sort_order = rt.get("sort_order", 0)
		doc.insert(ignore_permissions=True)

	# Backfill: set record_type = "Other" on every Tracora Infra Record
	# whose record_type is NULL or empty
	frappe.db.sql(
		"""
		UPDATE `tabTracora Infra Record`
		SET record_type = 'Other'
		WHERE record_type IS NULL OR record_type = ''
		"""
	)
