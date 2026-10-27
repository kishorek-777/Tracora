# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class TracoraInfraRecord(Document):
	def autoname(self):
		self.name = make_autoname("INF-.#####")

	def validate(self):
		cleaned_rows = []
		text_parts = []

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
			label = (row.field_label or "").strip()
			val = (row.field_value or "").strip()

			# b) If label AND value are both empty -> remove the row silently
			if not label and not val:
				continue

			# c) If label is empty but value is present -> set label to "Untitled Field"
			if not label and val:
				label = "Untitled Field"

			row.field_label = label
			row.field_value = val
			cleaned_rows.append(row)

			if val:
				if candidate_priority_title is None and label.lower() in priority_labels:
					candidate_priority_title = val
				if first_non_empty_value is None:
					first_non_empty_value = val

			if label:
				text_parts.append(label)
			if val:
				text_parts.append(val)

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

		# e) search_text computation
		self.search_text = " ".join(text_parts).lower()
