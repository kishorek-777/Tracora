# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraBranch(Document):
	def autoname(self):
		if not self.branch_name or not str(self.branch_name).strip():
			frappe.throw(_("Branch Name is required for autonaming."), frappe.ValidationError)

		clean_name = str(self.branch_name).strip()
		existing = frappe.db.get_value(
			"Tracora Branch",
			{"branch_name": clean_name, "name": ["!=", self.name or ""]},
			"name"
		)
		if not existing and frappe.db.exists("Tracora Branch", clean_name) and self.name != clean_name:
			existing = clean_name

		if existing:
			frappe.throw(
				_("Branch '{0}' already exists.").format(clean_name),
				frappe.DuplicateEntryError
			)

		self.name = clean_name
		self.branch_name = clean_name
