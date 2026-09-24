# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraAssetCategory(Document):
	def validate(self):
		if self.category_name:
			self.category_name = self.category_name.strip()
		if not self.category_name:
			frappe.throw(_("Category Name cannot be empty."), frappe.ValidationError)
