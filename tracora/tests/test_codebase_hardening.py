# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.api.portal import get_dashboard_summary, scan_asset, search_assets
from tracora.permissions import has_data_import_permission
from tracora.licences.roll_forward import calculate_next_renewal
from tracora.api.infra import search_records


class TestCodebaseHardening(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.created_users = []
		cls.created_docs = []

		# Create test non-tracora user
		cls.plain_user = cls.create_test_user("test_plain_hardening@example.com", ["HR User"])
		cls.admin_user = cls.create_test_user("test_admin_hardening@example.com", ["Tracora Admin"])

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for doc in cls.created_docs:
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
			"roles": [{"role": r} for r in roles if frappe.db.exists("Role", r)],
			"user_type": "System User",
			"send_welcome_email": 0,
		})
		user.insert(ignore_permissions=True)
		cls.created_users.append(email)
		return email

	def test_01_portal_security_guest_and_non_tracora_rejected(self):
		"""Portal endpoints refuse access to unauthenticated guests and non-Tracora users."""
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_dashboard_summary()

		frappe.set_user(self.plain_user)
		with self.assertRaises(frappe.PermissionError):
			get_dashboard_summary()
		with self.assertRaises(frappe.PermissionError):
			scan_asset("TRC-000001")
		with self.assertRaises(frappe.PermissionError):
			search_assets("Laptop")

	def test_02_portal_dashboard_status_assigned(self):
		"""Dashboard summary reflects assigned assets using correct status 'Assigned'."""
		frappe.set_user(self.admin_user)
		summary = get_dashboard_summary()["summary"]
		real_assigned = frappe.db.count("Tracora Asset", filters={"status": "Assigned"})
		self.assertEqual(summary["assigned_assets"], real_assigned)

	def test_03_has_data_import_permission_string_docname(self):
		"""has_data_import_permission correctly blocks non-Tracora reference doctype when doc is a string docname."""
		# Create a dummy Data Import for non-Tracora doctype
		frappe.set_user("Administrator")
		di = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "User",
			"import_type": "Insert New Records",
		})
		di.flags.ignore_permissions = True
		di.flags.ignore_mandatory = True
		di.insert(ignore_permissions=True)
		self.created_docs.append(di)

		# Check permission using string docname
		has_perm = has_data_import_permission(di.name, ptype="read", user=self.admin_user)
		self.assertFalse(has_perm, "Restricted Tracora Admin must not have permission on non-Tracora Data Import even when doc is passed as string")

	def test_04_roll_forward_invalid_cycle_returns_none(self):
		"""calculate_next_renewal returns None for invalid or non-recurring cycles."""
		self.assertIsNone(calculate_next_renewal("2026-01-01", "One-time"))
		self.assertIsNone(calculate_next_renewal("2026-01-01", ""))
		self.assertIsNone(calculate_next_renewal("2026-01-01", None))
		self.assertIsNone(calculate_next_renewal("2026-01-01", "InvalidCycle"))

	def test_05_infra_search_matches_id_and_title(self):
		"""search_records matches record by name (ID) and title directly."""
		frappe.set_user("Administrator")
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"record_type": "Other",
			"field_rows": [
				{"field_label": "Hostname", "field_value": "core-gw-blr"},
			]
		})
		rec.insert(ignore_permissions=True)
		self.created_docs.append(rec)

		# Search by record ID (rec.name, e.g. INF-00001)
		res_name = search_records(query=rec.name)
		matched_names = [r["name"] for r in res_name["records"]]
		self.assertIn(rec.name, matched_names)

		# Search by title
		res_title = search_records(query=rec.title)
		matched_titles = [r["name"] for r in res_title["records"]]
		self.assertIn(rec.name, matched_titles)
