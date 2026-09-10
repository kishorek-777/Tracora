# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraCompany(Document):
	def validate(self):
		if not self.company_type:
			frappe.throw(_("Company Type is required and must be selected (FR-70)."), frappe.ValidationError)

		if self.company_abbr:
			self.company_abbr = self.company_abbr.strip().upper()
			existing = frappe.db.get_value(
				"Tracora Company",
				{"company_abbr": self.company_abbr, "name": ["!=", self.name]},
				"company_name"
			)
			if existing:
				frappe.throw(
					_("Company Abbreviation '{0}' is already used by company '{1}'.").format(
						self.company_abbr, existing
					),
					frappe.DuplicateEntryError
				)
