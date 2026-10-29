# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTracoraVendor(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		# Clean up any leftover test vendors
		for v in ["Test Vendor Alpha", "Test Vendor Beta"]:
			if frappe.db.exists("Tracora Vendor", v):
				frappe.delete_doc("Tracora Vendor", v, force=True)
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")
		for v in ["Test Vendor Alpha", "Test Vendor Beta"]:
			if frappe.db.exists("Tracora Vendor", v):
				frappe.delete_doc("Tracora Vendor", v, force=True)
		frappe.db.commit()

	def test_01_vendor_creation_and_autoname(self):
		"""Vendor autonames to stripped vendor_name."""
		doc = frappe.get_doc({
			"doctype": "Tracora Vendor",
			"vendor_name": "  Test Vendor Alpha  ",
			"vendor_category": "Hardware OEM / Supplier",
			"status": "Active",
			"contact_email": "alpha@example.com",
		}).insert()

		self.assertEqual(doc.name, "Test Vendor Alpha")
		self.assertEqual(doc.vendor_name, "Test Vendor Alpha")
		self.assertEqual(doc.status, "Active")

	def test_02_duplicate_vendor_rejected_case_insensitively(self):
		"""Duplicate vendor names rejected regardless of casing."""
		frappe.get_doc({
			"doctype": "Tracora Vendor",
			"vendor_name": "Test Vendor Alpha",
			"vendor_category": "Hardware OEM / Supplier",
			"status": "Active",
		}).insert()

		with self.assertRaises(frappe.DuplicateEntryError):
			frappe.get_doc({
				"doctype": "Tracora Vendor",
				"vendor_name": "test vendor alpha",
				"vendor_category": "Telecom / Internet",
			}).insert()

	def test_03_invalid_email_rejected(self):
		"""Invalid email format throws ValidationError."""
		with self.assertRaises(frappe.InvalidEmailAddressError):
			frappe.get_doc({
				"doctype": "Tracora Vendor",
				"vendor_name": "Test Vendor Beta",
				"vendor_category": "SaaS / Cloud / Software",
				"contact_email": "invalid-email-address",
			}).insert()

	def test_04_no_delete_permission_in_docperm(self):
		"""Assert delete: 0 for all roles in DocPerm."""
		perms = frappe.get_all(
			"DocPerm",
			filters={"parent": "Tracora Vendor"},
			fields=["role", "delete"],
		)
		for p in perms:
			self.assertEqual(p.delete, 0, f"Role {p.role} must not have delete=1 on Tracora Vendor")
