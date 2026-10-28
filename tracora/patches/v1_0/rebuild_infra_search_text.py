# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from tracora.tracora.doctype.tracora_infra_record.tracora_infra_record import build_search_text


def execute():
	records = frappe.get_all("Tracora Infra Record", fields=["name", "search_text"])
	for r in records:
		rows = frappe.get_all(
			"Tracora Infra Field",
			filters={"parent": r.name, "parenttype": "Tracora Infra Record"},
			fields=["field_value"],
			order_by="idx asc",
		)
		new_search_text = build_search_text(rows)
		if (r.search_text or "") != new_search_text:
			frappe.db.set_value(
				"Tracora Infra Record",
				r.name,
				"search_text",
				new_search_text,
				update_modified=False,
			)
