# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.patches.v1_0.remove_super_admin_delete import execute as run_patch

# Expected snapshot for Tracora module doctypes
SNAPSHOT = {
	"Tracora Asset": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Asset Category": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Asset Movement": {"read": 1, "write": 0, "create": 1, "delete": 0},
	"Tracora Branch": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Company": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Department": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Employee": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Infra Category": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Infra Record": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Infra Record Type": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Location": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Maintenance Log": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Reminder Log": {"read": 1, "write": 0, "create": 0, "delete": 0},
	"Tracora Settings": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Software Licence": {"read": 1, "write": 1, "create": 1, "delete": 0},
	"Tracora Sync Conflict": {"read": 1, "write": 1, "create": 1, "delete": 0},
}


class TestSuperAdminNoDelete(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.created_users = []
		cls.created_docs = []

		# Ensure patch has been executed
		run_patch()

		cls.super_admin_user = cls.create_test_user(
			"test_super_no_del@example.com", ["Tracora Super Admin"]
		)
		cls.admin_user = cls.create_test_user(
			"test_admin_no_del@example.com", ["Tracora Admin"]
		)

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

	def test_01_super_admin_has_no_delete_on_all_tracora_doctypes(self):
		"""For every non-child doctype of Tracora module, Tracora Super Admin has no delete, but keeps read/write/create."""
		for dt, expected in SNAPSHOT.items():
			# Delete must be False
			can_delete = frappe.has_permission(dt, "delete", user=self.super_admin_user)
			self.assertFalse(can_delete, f"Tracora Super Admin must NOT have delete permission on {dt}")

			# Read must match expected
			can_read = frappe.has_permission(dt, "read", user=self.super_admin_user)
			self.assertEqual(bool(can_read), bool(expected["read"]), f"Read permission mismatch on {dt}")

			# Write must match expected
			can_write = frappe.has_permission(dt, "write", user=self.super_admin_user)
			self.assertEqual(bool(can_write), bool(expected["write"]), f"Write permission mismatch on {dt}")

			# Create must match expected
			can_create = frappe.has_permission(dt, "create", user=self.super_admin_user)
			self.assertEqual(bool(can_create), bool(expected["create"]), f"Create permission mismatch on {dt}")

	def test_02_admin_user_delete_and_other_permissions(self):
		"""Tracora Admin still has no delete on core asset/infra doctypes and keeps read/write/create."""
		core_doctypes = [
			"Tracora Asset",
			"Tracora Asset Category",
			"Tracora Asset Movement",
			"Tracora Infra Record",
			"Tracora Infra Category",
			"Tracora Infra Record Type",
			"Tracora Maintenance Log",
			"Tracora Reminder Log",
			"Tracora Settings",
			"Tracora Software Licence",
		]
		for dt in core_doctypes:
			can_delete = frappe.has_permission(dt, "delete", user=self.admin_user)
			self.assertFalse(can_delete, f"Tracora Admin must NOT have delete permission on {dt}")
			self.assertTrue(frappe.has_permission(dt, "read", user=self.admin_user), f"Admin must have read on {dt}")
			# Check write for non-log doctypes
			if SNAPSHOT[dt]["write"]:
				self.assertTrue(frappe.has_permission(dt, "write", user=self.admin_user), f"Admin must have write on {dt}")

	def test_03_patch_targets_only_super_admin_and_tracora_doctypes(self):
		"""Assert patch changes only rows of role Tracora Super Admin on Tracora module doctypes."""
		# Take counts for other roles
		other_roles_docperm = frappe.db.count("DocPerm", {"role": ["!=", "Tracora Super Admin"]})
		other_roles_custom = frappe.db.count("Custom DocPerm", {"role": ["!=", "Tracora Super Admin"]})

		# Take counts for non-Tracora doctypes
		tracora_dts = frappe.get_all("DocType", filters={"module": "Tracora"}, pluck="name")
		non_tracora_docperm = frappe.db.count("DocPerm", {"parent": ["not in", tracora_dts]})
		non_tracora_custom = frappe.db.count("Custom DocPerm", {"parent": ["not in", tracora_dts]})

		# Run patch
		run_patch()

		# Assert identical counts
		self.assertEqual(other_roles_docperm, frappe.db.count("DocPerm", {"role": ["!=", "Tracora Super Admin"]}))
		self.assertEqual(other_roles_custom, frappe.db.count("Custom DocPerm", {"role": ["!=", "Tracora Super Admin"]}))
		self.assertEqual(non_tracora_docperm, frappe.db.count("DocPerm", {"parent": ["not in", tracora_dts]}))
		self.assertEqual(non_tracora_custom, frappe.db.count("Custom DocPerm", {"parent": ["not in", tracora_dts]}))

	def test_04_patch_idempotence(self):
		"""Patch run twice gives identical rows."""
		# Get snapshot of all DocPerm and Custom DocPerm rows
		docperm_before = frappe.get_all("DocPerm", fields=["name", "parent", "role", "delete"])
		custom_before = frappe.get_all("Custom DocPerm", fields=["name", "parent", "role", "delete"])

		# Run patch again
		run_patch()

		docperm_after = frappe.get_all("DocPerm", fields=["name", "parent", "role", "delete"])
		custom_after = frappe.get_all("Custom DocPerm", fields=["name", "parent", "role", "delete"])

		self.assertEqual(docperm_before, docperm_after)
		self.assertEqual(custom_before, custom_after)

	def test_05_administrator_can_still_delete(self):
		"""Administrator can still delete a Tracora document."""
		frappe.set_user("Administrator")
		test_cat = frappe.get_doc({
			"doctype": "Tracora Asset Category",
			"category_name": "Test Throwaway Category For Admin Delete",
		}).insert()

		self.assertTrue(frappe.db.exists("Tracora Asset Category", test_cat.name))

		frappe.delete_doc("Tracora Asset Category", test_cat.name)
		self.assertFalse(frappe.db.exists("Tracora Asset Category", test_cat.name))
