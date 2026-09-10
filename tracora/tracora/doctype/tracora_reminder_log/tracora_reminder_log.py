# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraReminderLog(Document):
	def validate(self):
		if self.get_doc_before_save():
			frappe.throw(_("History records cannot be edited (NFR-03)."), frappe.ValidationError)

		if self.is_new():
			existing = frappe.db.exists(
				"Tracora Reminder Log",
				{
					"reference_doctype": self.reference_doctype,
					"reference_name": self.reference_name,
					"reminder_type": self.reminder_type,
					"due_date": self.due_date,
					"days_before": self.days_before,
					"recipient": self.recipient,
				},
			)
			if existing:
				frappe.throw(
					_("A reminder log already exists for this milestone and recipient."),
					frappe.DuplicateEntryError,
				)

	def on_trash(self):
		frappe.throw(_("History records cannot be deleted (NFR-03)."), frappe.ValidationError)


def on_doctype_update():
	frappe.db.add_unique(
		"Tracora Reminder Log",
		["reference_doctype", "reference_name", "reminder_type", "due_date", "days_before", "recipient"],
		constraint_name="unique_reminder_entry",
	)
