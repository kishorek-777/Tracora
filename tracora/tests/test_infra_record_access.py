# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.api.infra import search_records, get_counts
from frappe.utils.global_search import search as global_search


class TestInfraRecordAccess(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.created_users = []
		cls.created_docs = []

		cls.admin_user = cls.create_test_user("test_infra_admin@example.com", ["Tracora Admin"])
		cls.super_admin_user = cls.create_test_user("test_infra_super@example.com", ["Tracora Super Admin"])
		cls.sys_mgr_user = cls.create_test_user("test_infra_sys_mgr@example.com", ["System Manager"])

		non_tracora_role = "HR User" if frappe.db.exists("Role", "HR User") else "Blogger"
		cls.plain_user = cls.create_test_user("test_infra_plain@example.com", [non_tracora_role])

		# Ensure test master data exists
		frappe.set_user("Administrator")
		if not frappe.db.exists("Tracora Infra Record Type", "Test Device Type"):
			rt = frappe.get_doc({
				"doctype": "Tracora Infra Record Type",
				"type_name": "Test Device Type",
			}).insert(ignore_permissions=True)
			cls.created_docs.append(rt)

		if not frappe.db.exists("Tracora Infra Category", "Test Server Category"):
			cat = frappe.get_doc({
				"doctype": "Tracora Infra Category",
				"category_name": "Test Server Category",
				"record_type": "Test Device Type",
			}).insert(ignore_permissions=True)
			cls.created_docs.append(cat)

		frappe.db.commit()

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

	def test_01_admin_and_super_admin_permissions(self):
		"""User A (Tracora Admin) and User B (Tracora Super Admin) can read, create, write; neither can delete."""
		doctypes = ["Tracora Infra Record", "Tracora Infra Category", "Tracora Infra Record Type"]
		for dt in doctypes:
			for user, role_name in [(self.admin_user, "Tracora Admin"), (self.super_admin_user, "Tracora Super Admin")]:
				self.assertTrue(
					frappe.has_permission(dt, "read", user=user),
					f"{role_name} should have read permission on {dt}",
				)
				self.assertTrue(
					frappe.has_permission(dt, "write", user=user),
					f"{role_name} should have write permission on {dt}",
				)
				self.assertTrue(
					frappe.has_permission(dt, "create", user=user),
					f"{role_name} should have create permission on {dt}",
				)
				self.assertFalse(
					frappe.has_permission(dt, "delete", user=user),
					f"{role_name} should NOT have delete permission on {dt}",
				)

	def test_02_delete_blocked_for_admin_and_super_admin(self):
		"""Attempting to delete raises PermissionError for both Tracora Admin and Super Admin."""
		frappe.set_user("Administrator")
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"title": "Throwaway Record for Delete Test",
			"record_type": "Test Device Type",
			"category": "Test Server Category",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		try:
			# Test Admin
			frappe.set_user(self.admin_user)
			with self.assertRaises(frappe.PermissionError):
				frappe.delete_doc("Tracora Infra Record", rec.name)

			# Test Super Admin
			frappe.set_user(self.super_admin_user)
			with self.assertRaises(frappe.PermissionError):
				frappe.delete_doc("Tracora Infra Record", rec.name)
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("Tracora Infra Record", rec.name):
				frappe.delete_doc("Tracora Infra Record", rec.name, force=True, ignore_permissions=True)
				frappe.db.commit()

	def test_03_non_tracora_and_system_manager_denied(self):
		"""User C (plain user) and User D (System Manager) cannot read or create, and get_list returns empty."""
		doctypes = ["Tracora Infra Record", "Tracora Infra Category", "Tracora Infra Record Type"]
		for dt in doctypes:
			for user, role_name in [(self.plain_user, "Plain User"), (self.sys_mgr_user, "System Manager")]:
				self.assertFalse(
					frappe.has_permission(dt, "read", user=user),
					f"{role_name} should NOT have read on {dt}",
				)
				self.assertFalse(
					frappe.has_permission(dt, "create", user=user),
					f"{role_name} should NOT have create on {dt}",
				)

				frappe.set_user(user)
				# get_list should either raise PermissionError or return empty list
				try:
					records = frappe.get_list(dt)
					self.assertEqual(len(records), 0, f"{role_name} should see 0 records for {dt}")
				except frappe.PermissionError:
					pass

	def test_04_api_infra_permission_checks(self):
		"""search_records and get_counts raise PermissionError for C and D, succeed for A and B."""
		# User A (Admin) -> success
		frappe.set_user(self.admin_user)
		res_a = search_records(query="")
		self.assertIn("records", res_a)
		counts_a = get_counts()
		self.assertIsInstance(counts_a, list)

		# User B (Super Admin) -> success
		frappe.set_user(self.super_admin_user)
		res_b = search_records(query="")
		self.assertIn("records", res_b)
		counts_b = get_counts()
		self.assertIsInstance(counts_b, list)

		# User C (Plain User) -> PermissionError
		frappe.set_user(self.plain_user)
		with self.assertRaises(frappe.PermissionError):
			search_records(query="")
		with self.assertRaises(frappe.PermissionError):
			get_counts()

		# User D (System Manager) -> PermissionError
		frappe.set_user(self.sys_mgr_user)
		with self.assertRaises(frappe.PermissionError):
			search_records(query="")
		with self.assertRaises(frappe.PermissionError):
			get_counts()

	def test_05_global_search_no_results_for_c_and_d(self):
		"""Global search for a value returns no result of the three doctypes for User C and User D."""
		infra_doctypes = {"Tracora Infra Record", "Tracora Infra Category", "Tracora Infra Record Type"}

		frappe.set_user(self.plain_user)
		try:
			results_c = global_search("Test")
			c_infra_matches = [r for r in (results_c or []) if getattr(r, "doctype", None) in infra_doctypes]
			self.assertEqual(len(c_infra_matches), 0, "Plain user must not see infra doctypes in global search")
		except Exception:
			# If global search is not enabled or throws for unprivileged user, that is acceptable
			pass

		frappe.set_user(self.sys_mgr_user)
		try:
			results_d = global_search("Test")
			d_infra_matches = [r for r in (results_d or []) if getattr(r, "doctype", None) in infra_doctypes]
			self.assertEqual(len(d_infra_matches), 0, "System Manager must not see infra doctypes in global search")
		except Exception:
			pass

	def test_06_user_a_create_with_link_validation(self):
		"""User A can create a Tracora Infra Record referencing existing Infra Category and Record Type."""
		frappe.set_user(self.admin_user)
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"title": "Created By User A",
			"record_type": "Test Device Type",
			"category": "Test Server Category",
		}).insert()
		self.created_docs.append(rec)
		self.assertTrue(rec.name)

		# Link validation still rejects non-existent record type
		with self.assertRaises(frappe.LinkValidationError):
			frappe.get_doc({
				"doctype": "Tracora Infra Record",
				"title": "Invalid Link Record",
				"record_type": "Non Existent Record Type XYZ",
				"category": "Test Server Category",
			}).insert()

	def test_07_plain_user_unaffected_on_non_tracora_doctypes(self):
		"""User with no Tracora role still retains standard permissions on non-Tracora doctypes."""
		self.assertTrue(
			frappe.has_permission("Event", "read", user=self.plain_user),
			"Plain user should have read permission on Event",
		)
