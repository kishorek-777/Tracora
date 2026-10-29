# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import getdate, today


class TracoraAssetAuditLog(Document):
	def autoname(self):
		self.name = make_autoname("AUD-.#####")

	def validate(self):
		if not self.is_new():
			frappe.throw(_("Audit log entries are immutable and cannot be modified."), frappe.ValidationError)

		if not self.asset:
			frappe.throw(_("Asset is mandatory for audit log."), frappe.ValidationError)

		if not self.auditor:
			self.auditor = frappe.session.user

		if not self.auditor_name:
			self.auditor_name = frappe.utils.get_fullname(self.auditor) or self.auditor

		if not self.audit_date:
			self.audit_date = today()
		elif getdate(self.audit_date) > getdate(today()):
			frappe.throw(_("Audit date cannot be in the future."), frappe.ValidationError)

		if not self.remarks or not str(self.remarks).strip():
			frappe.throw(_("Audit remarks are mandatory."), frappe.ValidationError)

		if self.asset and not self.asset_name:
			self.asset_name = frappe.db.get_value("Tracora Asset", self.asset, "asset_name") or ""

	def after_insert(self):
		# Sync audit summary to Tracora Asset upon insertion
		if self.asset and frappe.db.exists("Tracora Asset", self.asset):
			frappe.flags.in_tracora_audit_sync = True
			try:
				asset_doc = frappe.get_doc("Tracora Asset", self.asset)
				asset_doc.audit_date = self.audit_date
				clean_remarks = (self.remarks or "").strip()
				status_prefix = f"[{self.audit_status}] " if not clean_remarks.startswith("[") else ""
				asset_doc.audit_remarks = f"{status_prefix}{clean_remarks}"
				if self.condition and asset_doc.condition != self.condition:
					asset_doc.condition = self.condition
				asset_doc.flags.ignore_permissions = True
				asset_doc.save()
			finally:
				frappe.flags.in_tracora_audit_sync = False

	def on_trash(self):
		frappe.throw(_("Audit log entries cannot be deleted."), frappe.ValidationError)
