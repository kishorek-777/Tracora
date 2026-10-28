# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.patches.v1_0.remove_admin_delete import execute as run_patch

# Snapshot of Tracora Admin permissions taken from git HEAD before this change
ADMIN_SNAPSHOT = {
	"Tracora Asset": {"read": 1, "write": 1, "create": 1, "export": 1, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Asset Category": {"read": 1, "write": 1, "create": 1, "export": 1, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Asset Movement": {"read": 1, "write": 0, "create": 1, "export": 1, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Branch": {"read": 1, "write": 1, "create": 1, "export": 0, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Company": {"read": 1, "write": 1, "create": 1, "export": 0, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Department": {"read": 1, "write": 1, "create": 1, "export": 0, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Employee": {"read": 1, "write": 1, "create": 1, "export": 0, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Infra Category": {"read": 1, "write": 1, "create": 1, "export": 1, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Infra Record": {"read": 1, "write": 1, "create": 1, "export": 1, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Infra Record Type": {"read": 1, "write": 1, "create": 1, "export": 1, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Location": {"read": 1, "write": 1, "create": 1, "export": 0, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Maintenance Log": {"read": 1, "write": 1, "create": 1, "export": 1, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Reminder Log": {"read": 1, "write": 0, "create": 0, "export": 1, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Settings": {"read": 1, "write": 1, "create": 1, "export": 0, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Software Licence": {"read": 1, "write": 1, "create": 1, "export": 1, "print": 1, "email": 1, "share": 1, "report": 1},
	"Tracora Sync Conflict": {"read": 1, "write": 1, "create": 1, "export": 0, "print": 1, "email": 1, "share": 1, "report": 1},
}


class TestNoDeleteInvariant(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.created_users = []
		cls.created_docs = []

		# Execute patch to ensure database is in expected state
		run_patch()

		cls.admin_user = cls.create_test_user("test_inv_admin@example.com", ["Tracora Admin"])
		cls.super_admin_user = cls.create_test_user("test_inv_super@example.com", ["Tracora Super Admin"])

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for doc in reversed(cls.created_docs):
			if frappe.db.exists(doc.doctype, doc.name):
				frappe.delete_doc(doc.doctype, doc.name, force=True, ignore_permissions=True)
		for email in cls.created_users:
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDownClass()

	@classmethod
	def create_test_user(cls, email, roles):
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)

		user = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
			"roles": [{"role": r} for r in roles],
		}).insert(ignore_permissions=True)
		cls.created_users.append(email)
		return email

	def test_01_db_driven_invariant_no_delete_on_tracora_doctypes(self):
		"""Assert ZERO rows with delete = 1 in tabDocPerm and tabCustom DocPerm for any role on Tracora doctypes."""
		tracora_dts = frappe.get_all("DocType", filters={"module": "Tracora"}, pluck="name")
		docperm_rows = frappe.get_all(
			"DocPerm",
			filters={"parent": ["in", tracora_dts], "delete": 1},
			fields=["parent", "role"],
		)
		custom_rows = frappe.get_all(
			"Custom DocPerm",
			filters={"parent": ["in", tracora_dts], "delete": 1},
			fields=["parent", "role"],
		)
		self.assertEqual(len(docperm_rows), 0, f"Found DocPerm rows with delete=1: {docperm_rows}")
		self.assertEqual(len(custom_rows), 0, f"Found Custom DocPerm rows with delete=1: {custom_rows}")

	def test_02_admin_and_super_admin_has_permission_delete_is_false(self):
		"""For user with only Tracora Admin and user with only Tracora Super Admin,
		frappe.has_permission(doctype, 'delete') is False for ALL non-child Tracora doctypes (including singles).
		"""
		non_child_doctypes = frappe.get_all(
			"DocType",
			filters={"module": "Tracora", "istable": 0},
			pluck="name",
		)
		for user in [self.admin_user, self.super_admin_user]:
			role_label = "Tracora Admin" if user == self.admin_user else "Tracora Super Admin"
			for dt in non_child_doctypes:
				can_delete = frappe.has_permission(dt, "delete", user=user)
				self.assertFalse(can_delete, f"{role_label} must NOT have delete permission on {dt}")

	def test_03_patch_scope(self):
		"""Assert patch changes only rows of role Tracora Admin on Tracora module doctypes."""
		# Record counts before patch
		other_roles_docperm = frappe.db.count("DocPerm", {"role": ["!=", "Tracora Admin"]})
		other_roles_custom = frappe.db.count("Custom DocPerm", {"role": ["!=", "Tracora Admin"]})

		tracora_dts = frappe.get_all("DocType", filters={"module": "Tracora"}, pluck="name")
		non_tracora_docperm = frappe.db.count("DocPerm", {"parent": ["not in", tracora_dts]})
		non_tracora_custom = frappe.db.count("Custom DocPerm", {"parent": ["not in", tracora_dts]})

		# Run patch
		run_patch()

		# Assert identical counts
		self.assertEqual(other_roles_docperm, frappe.db.count("DocPerm", {"role": ["!=", "Tracora Admin"]}))
		self.assertEqual(other_roles_custom, frappe.db.count("Custom DocPerm", {"role": ["!=", "Tracora Admin"]}))
		self.assertEqual(non_tracora_docperm, frappe.db.count("DocPerm", {"parent": ["not in", tracora_dts]}))
		self.assertEqual(non_tracora_custom, frappe.db.count("Custom DocPerm", {"parent": ["not in", tracora_dts]}))

	def test_04_patch_idempotence(self):
		"""Patch run twice gives identical rows."""
		run_patch()
		docperm_before = frappe.get_all("DocPerm", fields=["name", "parent", "role", "delete"])
		custom_before = frappe.get_all("Custom DocPerm", fields=["name", "parent", "role", "delete"])

		run_patch()
		docperm_after = frappe.get_all("DocPerm", fields=["name", "parent", "role", "delete"])
		custom_after = frappe.get_all("Custom DocPerm", fields=["name", "parent", "role", "delete"])

		self.assertEqual(docperm_before, docperm_after)
		self.assertEqual(custom_before, custom_after)

	def test_05_administrator_can_still_delete(self):
		"""Administrator can still delete a throwaway Tracora document."""
		frappe.set_user("Administrator")
		test_cat = frappe.get_doc({
			"doctype": "Tracora Asset Category",
			"category_name": "Test Throwaway Category Admin Invariant Delete",
		}).insert()

		self.assertTrue(frappe.db.exists("Tracora Asset Category", test_cat.name))

		frappe.delete_doc("Tracora Asset Category", test_cat.name)
		self.assertFalse(frappe.db.exists("Tracora Asset Category", test_cat.name))

	def test_06_admin_permissions_preserved(self):
		"""Assert read, write, create, export, print, email, share, report flags of Tracora Admin rows are identical to snapshot."""
		flags = ["read", "write", "create", "export", "print", "email", "share", "report"]
		for dt, expected in ADMIN_SNAPSHOT.items():
			perm_row = frappe.db.get_value(
				"DocPerm",
				{"parent": dt, "role": "Tracora Admin"},
				flags,
				as_dict=True,
			)
			self.assertIsNotNone(perm_row, f"No DocPerm row found for Tracora Admin on {dt}")
			for flag in flags:
				self.assertEqual(
					perm_row[flag],
					expected[flag],
					f"Flag {flag} mismatch for Tracora Admin on {dt}: expected {expected[flag]}, got {perm_row[flag]}",
				)
