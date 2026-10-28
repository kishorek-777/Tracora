# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

FALLBACK_TYPE = "Other"


def build_search_text(rows) -> str:
	"""
	Joins only the non-empty field_value strings (trimmed, lowercased) with a single space.
	Labels are NOT included.
	"""
	parts = []
	for row in rows or []:
		val = row.get("field_value") if isinstance(row, dict) else getattr(row, "field_value", None)
		if val and str(val).strip():
			parts.append(str(val).strip().lower())
	return " ".join(parts)


class TracoraInfraRecord(Document):
	def autoname(self):
		self.name = make_autoname("INF-.#####")

	def validate(self):
		# Fallback handling for record_type
		clean_type = (self.record_type or "").strip()
		if not clean_type:
			if frappe.db.exists("Tracora Infra Record Type", FALLBACK_TYPE):
				self.record_type = FALLBACK_TYPE
			else:
				self.record_type = ""
		else:
			self.record_type = clean_type

		cleaned_rows = []

		priority_labels = {
			"name",
			"device name",
			"connection name",
			"building name",
			"vendor name",
			"hostname",
		}

		candidate_priority_title = None
		first_non_empty_value = None

		for row in list(self.field_rows or []):
			raw_label = (row.field_label or "").strip()
			val = (row.field_value or "").strip()

			# b) If label AND value are both empty -> remove the row silently
			if not raw_label and not val:
				continue

			# c) If label is empty but value is present -> set label to "Untitled Field"
			if not raw_label and val:
				raw_label = "Untitled Field"

			# Cut label to 140 characters
			label = raw_label[:140]

			row.field_label = label
			row.field_value = row.field_value  # Full value stays untouched in field_value
			cleaned_rows.append(row)

			if val:
				# Use first line of chosen value, trimmed, cut to 140 characters
				first_line = val.split("\n", 1)[0].strip()[:140]
				if candidate_priority_title is None and label.lower() in priority_labels:
					candidate_priority_title = first_line
				if first_non_empty_value is None:
					first_non_empty_value = first_line

		# Re-index remaining rows sequentially
		for idx, row in enumerate(cleaned_rows, start=1):
			row.idx = idx

		self.field_rows = cleaned_rows

		# d) Title computation
		if candidate_priority_title:
			self.title = candidate_priority_title
		elif first_non_empty_value:
			self.title = first_non_empty_value
		else:
			self.title = "Untitled"

		# e) search_text computation (values only)
		self.search_text = build_search_text(self.field_rows)
