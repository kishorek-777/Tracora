# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraLocation(Document):
	@property
	def map_url(self):
		if self.latitude is not None and self.longitude is not None:
			return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
		return ""

	def validate(self):
		if self.latitude is None or not (-90.0 <= float(self.latitude) <= 90.0):
			frappe.throw(_("Latitude must be between -90 and 90 degrees (FR-03)."), frappe.ValidationError)

		if self.longitude is None or not (-180.0 <= float(self.longitude) <= 180.0):
			frappe.throw(_("Longitude must be between -180 and 180 degrees (FR-03)."), frappe.ValidationError)
