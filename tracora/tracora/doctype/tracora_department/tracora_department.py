# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraDepartment(Document):
	def autoname(self):
		if not self.department_name or not str(self.department_name).strip():
			frappe.throw(_("Department Name is required for autonaming."), frappe.ValidationError)

		clean_name = str(self.department_name).strip()
		existing = frappe.db.get_value(
			"Tracora Department",
			{"department_name": clean_name, "name": ["!=", self.name or ""]},
			"name"
		)
		if not existing and frappe.db.exists("Tracora Department", clean_name) and self.name != clean_name:
			existing = clean_name

		if existing:
			frappe.throw(
				_("Department '{0}' already exists.").format(clean_name),
				frappe.DuplicateEntryError
			)

		self.name = clean_name
		self.department_name = clean_name
