# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe

CATEGORIES = [
	{
		"category_name": "Internet / ISP",
		"record_type": "Device",
		"icon": "globe",
		"sort_order": 10,
		"fields": ["Connection Name", "Provider", "IP Address", "Bandwidth", "Account ID"],
	},
	{
		"category_name": "Firewall",
		"record_type": "Device",
		"icon": "shield",
		"sort_order": 20,
		"fields": ["Device Name", "Make", "Model", "Serial Number", "IP Address", "Firmware Version", "Location"],
	},
	{
		"category_name": "Switches",
		"record_type": "Device",
		"icon": "layers",
		"sort_order": 30,
		"fields": ["Device Name", "Make", "Model", "Serial Number", "IP Address", "Port Count", "Location"],
	},
	{
		"category_name": "Access Points",
		"record_type": "Device",
		"icon": "wifi",
		"sort_order": 40,
		"fields": ["Device Name", "Make", "Model", "IP Address", "SSID", "Location"],
	},
	{
		"category_name": "CCTV",
		"record_type": "Device",
		"icon": "video",
		"sort_order": 50,
		"fields": ["Camera Name", "Make", "Model", "IP Address", "Channel", "Location"],
	},
	{
		"category_name": "Biometric",
		"record_type": "Device",
		"icon": "fingerprint",
		"sort_order": 60,
		"fields": ["Device Name", "Make", "Model", "IP Address", "Serial Number", "Location"],
	},
	{
		"category_name": "Building",
		"record_type": "Building",
		"icon": "building",
		"sort_order": 70,
		"fields": ["Building Name", "Address", "City", "Number of Floors", "Contact Person", "Contact Number"],
	},
	{
		"category_name": "Vendor",
		"record_type": "Vendor",
		"icon": "store",
		"sort_order": 80,
		"fields": ["Vendor Name", "Contact Person", "Mobile", "Email", "Service Provided", "Contract Expiry"],
	},
]


def execute():
	for cat in CATEGORIES:
		name = cat["category_name"]
		# Idempotent: Never update an existing category
		if frappe.db.exists("Tracora Infra Category", name) or frappe.db.exists("Tracora Infra Category", {"category_name": name}):
			continue

		doc = frappe.new_doc("Tracora Infra Category")
		doc.category_name = name
		doc.record_type = cat["record_type"]
		doc.icon = cat.get("icon")
		doc.sort_order = cat.get("sort_order", 0)
		for label in cat["fields"]:
			doc.append("template_fields", {"field_label": label})
		doc.insert(ignore_permissions=True)
