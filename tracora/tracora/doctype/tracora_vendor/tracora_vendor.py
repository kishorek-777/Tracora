# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import validate_email_address


class TracoraVendor(Document):
	def autoname(self):
		if not self.vendor_name or not self.vendor_name.strip():
			frappe.throw(_("Vendor Name is mandatory."), frappe.MandatoryError)

		clean_name = self.vendor_name.strip()
		existing = frappe.db.sql(
			"SELECT name FROM `tabTracora Vendor` WHERE LOWER(name) = LOWER(%s) AND name != %s LIMIT 1",
			(clean_name, self.name or ""),
			as_dict=True,
		)
		if existing:
			frappe.throw(
				_("Vendor '{0}' already exists as '{1}'.").format(clean_name, existing[0].name),
				frappe.DuplicateEntryError,
			)

		self.name = clean_name

	def validate(self):
		if self.vendor_name:
			self.vendor_name = self.vendor_name.strip()

		if self.contact_email and self.contact_email.strip():
			self.contact_email = self.contact_email.strip()
			validate_email_address(self.contact_email, throw=True)

