# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TracoraAssetMovement(Document):
	def validate(self):
		if self.get_doc_before_save():
			frappe.throw(_('History records cannot be edited (FR-17).'), frappe.ValidationError)

		if not self.recorded_by:
			self.recorded_by = frappe.session.user

		if not self.movement_date:
			self.movement_date = frappe.utils.now_datetime()

		if self.movement_type in ('Unassign', 'Exit Release'):
			if not self.remarks or not str(self.remarks).strip():
				frappe.throw(
					_('Remarks are mandatory on {0} (FR-51).').format(self.movement_type),
					frappe.ValidationError
				)

	def on_trash(self):
		frappe.throw(_('History records cannot be deleted (FR-17).'), frappe.ValidationError)
