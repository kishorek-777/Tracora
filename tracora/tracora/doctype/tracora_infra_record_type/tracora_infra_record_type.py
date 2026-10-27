# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

FALLBACK_TYPE = "Other"


class TracoraInfraRecordType(Document):
	def autoname(self):
		base_name = (self.type_name or "").strip()
		if not base_name:
			base_name = "Untitled Type"

		name = base_name
		count = 1
		while frappe.db.exists("Tracora Infra Record Type", name):
			count += 1
			name = f"{base_name} {count}"
		self.name = name

	def validate(self):
		if self.type_name and self.type_name.strip():
			clean_type_name = self.type_name.strip()
			self.type_name = clean_type_name
			existing = frappe.db.sql(
				"""
				SELECT name FROM `tabTracora Infra Record Type`
				WHERE LOWER(type_name) = %s AND name != %s
				""",
				(clean_type_name.lower(), self.name or ""),
			)
			if existing:
				frappe.throw(
					_("Record Type '{0}' already exists.").format(clean_type_name),
					frappe.ValidationError,
				)
		elif self.type_name is not None:
			self.type_name = self.type_name.strip()

	def on_trash(self):
		if self.name == FALLBACK_TYPE:
			frappe.throw(
				_("{0} is the built-in fallback type and cannot be deleted").format(FALLBACK_TYPE),
				frappe.ValidationError,
			)

		rec_count = frappe.db.count("Tracora Infra Record", {"record_type": self.name})
		cat_count = frappe.db.count("Tracora Infra Category", {"record_type": self.name})

		if rec_count or cat_count:
			frappe.throw(
				_(
					"Cannot delete Record Type '{0}'. It is used by {1} record(s) and {2} category(ies)."
				).format(self.name, rec_count, cat_count),
				frappe.ValidationError,
			)
