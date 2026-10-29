# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _

ALLOWED_IMPORT_DOCTYPES = ["Tracora Asset", "Tracora Software Licence"]


def is_restricted_user(user=None) -> bool:
	"""
	Definition: a "restricted user" for Data Import =
	a user who has the role "Tracora Admin" OR "Tracora Super Admin"
	AND does NOT have the role "System Manager"
	AND is not Administrator.
	"""
	user = user or frappe.session.user
	if not user or user == "Administrator":
		return False

	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return False

	return bool(roles & {"Tracora Admin", "Tracora Super Admin"})


is_tracora_restricted_import_user = is_restricted_user


def get_data_import_query_conditions(user=None, doctype=None) -> str | None:
	"""
	permission_query_conditions hook for Data Import.
	For restricted users: limits rows to imports whose reference_doctype belongs
	to the Tracora module.
	For everyone else: returns None (no extra condition).
	"""
	if is_restricted_user(user):
		return "`tabData Import`.reference_doctype IN (SELECT name FROM `tabDocType` WHERE module = 'Tracora')"
	return None


def has_data_import_permission(doc, ptype="read", user=None, debug=False) -> bool:
	"""
	has_permission hook for Data Import.
	For restricted users:
	  - Disallow delete on Data Import.
	  - Deny access if reference_doctype is set and does not belong to module Tracora.
	  - Never deny when reference_doctype is empty (e.g. creating new document).
	For everyone else / when permitted: return True as required by Frappe's has_permission check.
	"""
	user = user or frappe.session.user
	if is_restricted_user(user):
		if ptype == "delete":
			return False

		if isinstance(doc, str):
			ref_dt = frappe.db.get_value("Data Import", doc, "reference_doctype")
		else:
			ref_dt = getattr(doc, "reference_doctype", None)
		if ref_dt:
			module = frappe.db.get_value("DocType", ref_dt, "module")
			if module != "Tracora":
				return False

	return True


def validate_data_import(doc, method=None):
	"""
	doc_events validate hook for Data Import.
	For restricted users: throw frappe.PermissionError if reference_doctype
	is empty or not in the allowed Tracora importable list.
	For everyone else: untouched.
	"""
	if is_restricted_user(frappe.session.user):
		if not doc.reference_doctype:
			frappe.throw(
				_("Document Type is required for Data Import."),
				frappe.PermissionError,
			)

		if doc.reference_doctype not in ALLOWED_IMPORT_DOCTYPES:
			frappe.throw(
				_("Data Import is only allowed for: {0}.").format(", ".join(ALLOWED_IMPORT_DOCTYPES)),
				frappe.PermissionError,
			)


@frappe.whitelist()
def get_allowed_import_doctypes() -> list[str]:
	"""
	Whitelisted helper returning the list of Tracora doctypes allowed for Data Import.
	"""
	return ALLOWED_IMPORT_DOCTYPES


def has_asset_audit_log_permission(doc, ptype="read", user=None, debug=False) -> bool:
	"""
	Audit logs are append-only.
	Creation/insertion is allowed, but once an audit log document exists (persisted/not new),
	'write' and 'delete' are strictly disallowed across all non-system roles.
	"""
	if ptype in ("write", "delete"):
		user = user or frappe.session.user
		if user and user != "Administrator":
			is_new = False
			if hasattr(doc, "is_new"):
				is_new = doc.is_new()
			elif isinstance(doc, str):
				is_new = False
			if not is_new:
				return False
	return True

