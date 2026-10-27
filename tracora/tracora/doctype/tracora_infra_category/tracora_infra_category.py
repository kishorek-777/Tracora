# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraInfraCategory(Document):
	def autoname(self):
		base_name = (self.category_name or "").strip()
		if not base_name:
			base_name = "Untitled Category"

		name = base_name
		count = 1
		while frappe.db.exists("Tracora Infra Category", name):
			count += 1
			name = f"{base_name} {count}"
		self.name = name

	def validate(self):
		if self.category_name and self.category_name.strip():
			clean_cat_name = self.category_name.strip()
			self.category_name = clean_cat_name
			existing = frappe.db.sql(
				"""
				SELECT name FROM `tabTracora Infra Category`
				WHERE LOWER(category_name) = %s AND name != %s
				""",
				(clean_cat_name.lower(), self.name or ""),
			)
			if existing:
				frappe.throw(
					_("Category Name '{0}' already exists in Category '{1}'.").format(
						clean_cat_name, existing[0][0]
					),
					frappe.ValidationError,
				)

	def on_trash(self):
		count = frappe.db.count("Tracora Infra Record", {"category": self.name})
		if count:
			frappe.throw(
				_("Cannot delete category '{0}' because it is used by {1} Infra Record(s).").format(
					self.name, count
				),
				frappe.ValidationError,
			)
