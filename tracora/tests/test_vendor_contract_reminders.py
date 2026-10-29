# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, today
from tracora.reminders.scheduler import (
	check_vendor_contract_reminders,
	get_active_recipients,
	parse_lead_days,
)


class TestVendorContractReminders(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("Tracora Vendor", "Test Reminder Vendor"):
			frappe.get_doc({
				"doctype": "Tracora Vendor",
				"vendor_name": "Test Reminder Vendor",
				"vendor_category": "Telecom / Internet",
				"status": "Active",
			}).insert()
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		if frappe.db.exists("Tracora Vendor", "Test Reminder Vendor"):
			frappe.delete_doc("Tracora Vendor", "Test Reminder Vendor", force=True)
		frappe.db.commit()
		super().tearDownClass()

	def tearDown(self):
		frappe.set_user("Administrator")
		contracts = frappe.get_all(
			"Tracora Vendor Contract",
			filters={"vendor": "Test Reminder Vendor"},
			pluck="name",
		)
		for c in contracts:
			frappe.db.sql("DELETE FROM `tabTracora Reminder Log` WHERE reference_name = %s", (c,))
			frappe.delete_doc("Tracora Vendor Contract", c, force=True)
		frappe.db.commit()

	def test_01_upcoming_renewal_reminder_dispatched_and_idempotent(self):
		"""Upcoming milestone creates Tracora Reminder Log row and is idempotent."""
		settings = frappe.get_single("Tracora Settings")
		lead_days = parse_lead_days(settings)
		recipients = get_active_recipients()
		today_date = getdate(today())

		target_lead = 7
		self.assertIn(target_lead, lead_days)

		doc = frappe.get_doc({
			"doctype": "Tracora Vendor Contract",
			"contract_title": "Upcoming Leased Line",
			"vendor": "Test Reminder Vendor",
			"category": "Telecom / Internet",
			"renewal_frequency": "Annually",
			"expected_amount": 50000,
			"next_renewal_date": add_days(today(), target_lead),
		}).insert()

		# Run check
		check_vendor_contract_reminders(lead_days, recipients, today_date)

		# Check Reminder Log
		logs = frappe.get_all(
			"Tracora Reminder Log",
			filters={
				"reference_doctype": "Tracora Vendor Contract",
				"reference_name": doc.name,
				"reminder_type": "Vendor Contract Renewal",
				"days_before": target_lead,
			},
			fields=["name", "recipient", "delivery_status"],
		)
		self.assertGreaterEqual(len(logs), 1)

		# Run again -> assert no duplicate logs created
		initial_count = len(logs)
		check_vendor_contract_reminders(lead_days, recipients, today_date)
		second_count = frappe.db.count(
			"Tracora Reminder Log",
			{
				"reference_doctype": "Tracora Vendor Contract",
				"reference_name": doc.name,
				"reminder_type": "Vendor Contract Renewal",
				"days_before": target_lead,
			},
		)
		self.assertEqual(initial_count, second_count)

	def test_02_overdue_renewal_dispatched_once(self):
		"""Overdue contract sets status to Overdue and logs days_before = -1 once."""
		settings = frappe.get_single("Tracora Settings")
		lead_days = parse_lead_days(settings)
		recipients = get_active_recipients()
		today_date = getdate(today())

		doc = frappe.get_doc({
			"doctype": "Tracora Vendor Contract",
			"contract_title": "Expired Server AMC",
			"vendor": "Test Reminder Vendor",
			"category": "Hardware AMC",
			"renewal_frequency": "Annually",
			"expected_amount": 30000,
			"next_renewal_date": add_days(today(), -5),
		}).insert()

		# Run check
		check_vendor_contract_reminders(lead_days, recipients, today_date)

		doc.reload()
		self.assertEqual(doc.renewal_status, "Overdue")

		overdue_logs = frappe.get_all(
			"Tracora Reminder Log",
			filters={
				"reference_doctype": "Tracora Vendor Contract",
				"reference_name": doc.name,
				"days_before": -1,
			},
		)
		self.assertGreaterEqual(len(overdue_logs), 1)

		# Second run idempotency
		initial_count = len(overdue_logs)
		check_vendor_contract_reminders(lead_days, recipients, today_date)
		second_count = frappe.db.count(
			"Tracora Reminder Log",
			{
				"reference_doctype": "Tracora Vendor Contract",
				"reference_name": doc.name,
				"days_before": -1,
			},
		)
		self.assertEqual(initial_count, second_count)

	def test_03_additional_recipient_notified(self):
		"""Additional recipients receive reminder logs along with admins."""
		settings = frappe.get_single("Tracora Settings")
		lead_days = parse_lead_days(settings)
		recipients = get_active_recipients()
		today_date = getdate(today())

		doc = frappe.get_doc({
			"doctype": "Tracora Vendor Contract",
			"contract_title": "Extra Notify Contract",
			"vendor": "Test Reminder Vendor",
			"category": "Software / SaaS Subscription",
			"renewal_frequency": "Monthly",
			"expected_amount": 12000,
			"next_renewal_date": add_days(today(), 1),
			"additional_recipients": "finance_dept@example.com",
		}).insert()

		check_vendor_contract_reminders(lead_days, recipients, today_date)

		extra_log = frappe.get_all(
			"Tracora Reminder Log",
			filters={
				"reference_doctype": "Tracora Vendor Contract",
				"reference_name": doc.name,
				"recipient": "finance_dept@example.com",
			},
		)
		self.assertEqual(len(extra_log), 1)
