# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraBranch(Document):
	def autoname(self):
		if not self.branch_name or not self.company:
			frappe.throw(_("Branch Name and Company are required for autonaming."), frappe.ValidationError)

		company_abbr = frappe.db.get_value("Tracora Company", self.company, "company_abbr")
		if not company_abbr:
			frappe.throw(_("Company '{0}' does not have an abbreviation set.").format(self.company), frappe.ValidationError)

		qualified_name = f"{self.branch_name.strip()} - {company_abbr.strip()}"
		if frappe.db.exists("Tracora Branch", qualified_name):
			frappe.throw(
				_("Branch '{0}' already exists for company '{1}' ({2}).").format(
					self.branch_name.strip(), self.company, company_abbr.strip()
				),
				frappe.DuplicateEntryError
			)
		self.name = qualified_name
