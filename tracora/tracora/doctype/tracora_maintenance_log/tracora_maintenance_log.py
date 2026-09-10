# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class TracoraMaintenanceLog(Document):
	def validate(self):
		# 1. Ensure recorded_by is set
		if not self.recorded_by or self.recorded_by == "user":
			self.recorded_by = frappe.session.user or "Administrator" 

		# 2. Guard against reopening or modifying a closed log
		old_doc = self.get_doc_before_save()
		if old_doc and old_doc.log_status in ("Closed", "Beyond Repair"):
			if self.log_status != old_doc.log_status:
				frappe.throw(
					_("Maintenance log '{0}' has already been finalized as '{1}' and cannot be reopened or modified.").format(
						self.name, old_doc.log_status
					),
					frappe.ValidationError
				)

		# 3. Model-level duplicate open log guard (works even if bypassing the API)
		if self.log_status == "Open":
			filters = {
				"asset": self.asset,
				"log_status": "Open",
			}
			if not self.is_new():
				filters["name"] = ["!=", self.name]

			existing_open_log = frappe.db.get_value("Tracora Maintenance Log", filters, "name")
			if existing_open_log:
				frappe.throw(
					_("Asset '{0}' already has an active open maintenance log ({1}). Multiple open logs for the same asset are refused.").format(
						self.asset, existing_open_log
					),
					frappe.ValidationError
				)

		# 4. Enforce return validation when closing
		if self.log_status in ("Closed", "Beyond Repair"):
			if not self.date_returned:
				self.date_returned = today()

			if self.log_status == "Closed" and not self.condition_on_return:
				frappe.throw(
					_("Condition on return is required when closing maintenance (FR-18)."),
					frappe.ValidationError
				)