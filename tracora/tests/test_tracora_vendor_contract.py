# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, add_years, getdate, today


class TestTracoraVendorContract(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		# Create Active Vendor
		if not frappe.db.exists("Tracora Vendor", "Test Active Vendor"):
			frappe.get_doc({
				"doctype": "Tracora Vendor",
				"vendor_name": "Test Active Vendor",
				"vendor_category": "Telecom / Internet",
				"status": "Active",
			}).insert()

		# Create Inactive Vendor
		if not frappe.db.exists("Tracora Vendor", "Test Inactive Vendor"):
			frappe.get_doc({
				"doctype": "Tracora Vendor",
				"vendor_name": "Test Inactive Vendor",
				"vendor_category": "Hardware OEM / Supplier",
				"status": "Inactive",
			}).insert()
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for v in ["Test Active Vendor", "Test Inactive Vendor"]:
			if frappe.db.exists("Tracora Vendor", v):
				frappe.delete_doc("Tracora Vendor", v, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def tearDown(self):
		frappe.set_user("Administrator")
		contracts = frappe.get_all(
			"Tracora Vendor Contract",
			filters={"vendor": ["in", ["Test Active Vendor", "Test Inactive Vendor"]]},
			pluck="name",
		)
		for c in contracts:
			frappe.delete_doc("Tracora Vendor Contract", c, force=True)
		frappe.db.commit()

	def test_01_contract_creation_and_autoname(self):
		"""Contract autonames to TRC-VCON-##### and sets Upcoming status."""
		doc = frappe.get_doc({
			"doctype": "Tracora Vendor Contract",
			"contract_title": "Primary Internet 200Mbps",
			"vendor": "Test Active Vendor",
			"category": "Telecom / Internet",
			"renewal_frequency": "Annually",
			"expected_amount": 60000,
			"next_renewal_date": add_days(today(), 60),
		}).insert()

		self.assertTrue(doc.name.startswith("TRC-VCON-"))
		self.assertEqual(doc.renewal_status, "Upcoming")
		self.assertEqual(doc.currency, "INR")

	def test_02_inactive_vendor_rejected(self):
		"""Contract creation rejected if vendor is inactive."""
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "Tracora Vendor Contract",
				"contract_title": "Invalid AMC Contract",
				"vendor": "Test Inactive Vendor",
				"category": "Hardware AMC",
				"renewal_frequency": "Annually",
			}).insert()

	def test_03_log_payment_advances_renewal_date_annually(self):
		"""Calling log_payment records row in child table and advances next_renewal_date by 1 year."""
		due_date = add_days(today(), 5)
		doc = frappe.get_doc({
			"doctype": "Tracora Vendor Contract",
			"contract_title": "Cisco Firewall Support",
			"vendor": "Test Active Vendor",
			"category": "Hardware AMC",
			"renewal_frequency": "Annually",
			"expected_amount": 45000,
			"next_renewal_date": due_date,
		}).insert()

		self.assertEqual(doc.renewal_status, "Due Soon")

		res = doc.log_payment(
			payment_date=today(),
			amount_paid=45000,
			payment_mode="Bank Transfer / NEFT",
			reference_no="UTR-TEST-99988",
			remarks="Renewed for next year",
		)

		self.assertTrue(res.get("success"))
		doc.reload()

		# Check payment row
		self.assertEqual(len(doc.payment_history), 1)
		row = doc.payment_history[0]
		self.assertEqual(row.amount_paid, 45000)
		self.assertEqual(row.reference_no, "UTR-TEST-99988")
		self.assertEqual(row.recorded_by, "Administrator")

		# Check advanced date (+1 year)
		expected_next = add_years(due_date, 1)
		self.assertEqual(str(doc.next_renewal_date), str(expected_next))
		self.assertEqual(doc.renewal_status, "Upcoming")

	def test_04_one_off_frequency_completes_cycle(self):
		"""One-off payment marks status as Completed / One-off without renewal date."""
		doc = frappe.get_doc({
			"doctype": "Tracora Vendor Contract",
			"contract_title": "Server Cable Replacement",
			"vendor": "Test Active Vendor",
			"category": "One-off Purchase",
			"renewal_frequency": "One-off / Non-recurring",
			"expected_amount": 5000,
		}).insert()

		res = doc.log_payment(
			payment_date=today(),
			amount_paid=5000,
			payment_mode="UPI",
			reference_no="UPI-TEST-12345",
		)
		self.assertTrue(res.get("success"))
		doc.reload()
		self.assertEqual(doc.renewal_status, "Completed / One-off")
		self.assertIsNone(doc.next_renewal_date)

	def test_05_amount_greater_than_zero_enforced(self):
		"""Amount <= 0 is rejected."""
		doc = frappe.get_doc({
			"doctype": "Tracora Vendor Contract",
			"contract_title": "Zero Test",
			"vendor": "Test Active Vendor",
			"category": "Other",
			"renewal_frequency": "Monthly",
		}).insert()

		with self.assertRaises(frappe.ValidationError):
			doc.log_payment(payment_date=today(), amount_paid=0)
