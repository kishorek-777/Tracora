# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraSettings(Document):
	def validate(self):
		self.validate_reminder_lead_days()

	def validate_reminder_lead_days(self):
		if not self.reminder_lead_days or not str(self.reminder_lead_days).strip():
			self.reminder_lead_days = "30,15,7,2,1,0"
			return

		parts = [p.strip() for p in str(self.reminder_lead_days).split(",") if p.strip()]
		if not parts:
			self.reminder_lead_days = "30,15,7,2,1,0"
			return

		valid_ints = []
		for part in parts:
			if not part.isdigit():
				frappe.throw(
					_("Reminder Lead Days must be comma-separated non-negative integers (e.g. '30,15,7,2,1,0'). Invalid value: '{0}'").format(part),
					frappe.ValidationError,
				)
			valid_ints.append(int(part))

		# Remove duplicates while preserving or sorting descending
		seen = set()
		unique_ints = []
		for x in valid_ints:
			if x not in seen:
				seen.add(x)
				unique_ints.append(x)

		self.reminder_lead_days = ",".join(str(x) for x in unique_ints)
