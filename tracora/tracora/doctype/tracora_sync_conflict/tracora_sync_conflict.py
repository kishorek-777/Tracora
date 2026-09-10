# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraSyncConflict(Document):
	@frappe.whitelist(methods=["POST"])
	def resolve(self):
		self.check_permission("write")
		self.conflict_status = "Resolved"
		self.save()
		return self
