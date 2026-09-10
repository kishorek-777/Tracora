# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import (
	add_days,
	add_months,
	getdate,
	now_datetime,
	today,
)
from unittest.mock import patch

from tracora.reminders.scheduler import (
	check_scheduler_health,
	get_active_recipients,
	run_daily_reminders,
)
from tracora.licences.roll_forward import advance_date_by_cycle


class TestTracoraReminders(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.company_name = "Licence Test Corp"
		if not frappe.db.exists("Tracora Company", self.company_name):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": self.company_name,
				"company_type": "Internal",
				"company_abbr": "LTC",
				"company_address": "789 Software Way, Chennai",
				"source": "Tracora",
			}).insert(ignore_permissions=True)

		# Ensure at least one enabled Tracora Admin user exists for tests
		self.admin_email = "test_reminder_admin@example.com"
		if not frappe.db.exists("User", self.admin_email):
			user = frappe.get_doc({
				"doctype": "User",
				"email": self.admin_email,
				"first_name": "Reminder",
				"last_name": "Admin",
				"enabled": 1,
				"user_type": "System User",
				"roles": [{"role": "Tracora Admin"}],
			}).insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", self.admin_email)
			user.enabled = 1
			if not any(r.role == "Tracora Admin" for r in user.roles):
				user.append("roles", {"role": "Tracora Admin"})
			user.save(ignore_permissions=True)

		# Reset settings to default
		settings = frappe.get_single("Tracora Settings")
		settings.reminder_lead_days = "30,15,7,2,1,0"
		settings.last_reminder_run = now_datetime()
		settings.save(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		# Reset settings back to standard default
		settings = frappe.get_single("Tracora Settings")
		settings.reminder_lead_days = "30,15,7,2,1,0"
		settings.save(ignore_permissions=True)

		# Clear reminder logs created during tests
		frappe.db.delete("Tracora Reminder Log", {"reference_doctype": "Tracora Software Licence"})
		frappe.db.commit()

	def _create_licence(self, **kwargs):
		prefix = frappe.generate_hash(length=6)
		doc_data = {
			"doctype": "Tracora Software Licence",
			"software_name": f"Test Software {prefix}",
			"licence_name": f"Test Licence {prefix}",
			"company": self.company_name,
			"licence_type": "User licence",
			"renewal_cycle": "One-time",
			"licence_start_date": today(),
			"licence_expiry_date": add_days(today(), 30),
			"seats": [],
		}
		doc_data.update(kwargs)
		lic = frappe.get_doc(doc_data)
		lic.insert(ignore_permissions=True)
		return lic

	def test_fr26_upcoming_milestones(self):
		"""
		FR-26: A licence due in 30 days produces reminders on lead day 30,
		and no duplicate when not on a lead day (e.g. 29).
		"""
		lic = self._create_licence(licence_expiry_date=add_days(today(), 30))
		initial_logs = frappe.db.count("Tracora Reminder Log", {"reference_name": lic.name})
		self.assertEqual(initial_logs, 0)

		# Day 30 is in default lead days (30,15,7,2,1,0)
		run_daily_reminders()

		logs_30 = frappe.get_all(
			"Tracora Reminder Log",
			filters={
				"reference_name": lic.name,
				"reminder_type": "Licence Expiry",
				"days_before": 30,
			},
			fields=["name", "recipient", "days_before", "delivery_status"],
		)
		self.assertGreaterEqual(len(logs_30), 1)
		recipients_logged = [l.recipient for l in logs_30]
		self.assertIn(self.admin_email, recipients_logged)

		# Simulate day 29 (not a lead day)
		frappe.db.set_value("Tracora Software Licence", lic.name, "licence_expiry_date", add_days(today(), 29))
		lic.reload()

		run_daily_reminders()

		logs_29 = frappe.get_all(
			"Tracora Reminder Log",
			filters={
				"reference_name": lic.name,
				"days_before": 29,
			},
		)
		self.assertEqual(len(logs_29), 0)

	def test_fr89_overdue_past_expiry_exact_one_notice(self):
		"""
		FR-89: A licence whose expiry has already passed produces exactly ONE
		overdue notice (days_before = -1) per recipient, and subsequent runs
		on the same or following days do not create duplicates.
		"""
		lic = self._create_licence(licence_expiry_date=add_days(today(), -10))

		# First run: should dispatch overdue notice
		run_daily_reminders()

		overdue_logs = frappe.get_all(
			"Tracora Reminder Log",
			filters={
				"reference_name": lic.name,
				"reminder_type": "Licence Expiry",
				"days_before": -1,
			},
			fields=["name", "recipient", "days_before"],
		)
		self.assertGreaterEqual(len(overdue_logs), 1)
		initial_count = len(overdue_logs)

		# Re-run immediately on same day: must produce ZERO duplicates
		run_daily_reminders()
		overdue_logs_after = frappe.get_all(
			"Tracora Reminder Log",
			filters={
				"reference_name": lic.name,
				"reminder_type": "Licence Expiry",
				"days_before": -1,
			},
		)
		self.assertEqual(len(overdue_logs_after), initial_count)

		# Simulate subsequent day (tomorrow): still ZERO new overdue logs
		with patch("tracora.reminders.scheduler.today", return_value=str(add_days(today(), 1))):
			run_daily_reminders()

		self.assertEqual(
			frappe.db.count("Tracora Reminder Log", {"reference_name": lic.name, "days_before": -1}),
			initial_count
		)

	def test_fr63_fr65_dynamic_renewal_date_advance_and_stale_log_isolation(self):
		"""
		FR-63, FR-65: Verify that reminder logs keyed to an old next_renewal_date do NOT 
		prevent reminders from firing against a newly-advanced next_renewal_date.
		"""
		# 1. Setup Monthly licence where next renewal is due today (milestone 0)
		licence = self._create_licence(
			renewal_cycle="Monthly",
			licence_start_date=today(),
			licence_expiry_date=add_months(today(), 12),
		)
		self.assertEqual(getdate(licence.next_renewal_date), getdate(today()))

		# 2. Run daily reminders: asserts log created for due_date = today(), days_before = 0
		run_daily_reminders()
		logs = frappe.get_all(
			"Tracora Reminder Log",
			filters={"reference_name": licence.name, "due_date": today(), "days_before": 0}
		)
		self.assertGreaterEqual(len(logs), 1)

		# 3. Simulate checkpoint crossing: advance next_renewal_date forward by 1 cycle
		new_due_date = advance_date_by_cycle(today(), "Monthly")
		frappe.db.set_value("Tracora Software Licence", licence.name, "next_renewal_date", new_due_date)
		licence.reload()

		# 4. Fast forward to milestone of new cycle (7 days before new_due_date)
		simulated_today = add_days(new_due_date, -7)
		with patch("tracora.reminders.scheduler.today", return_value=str(simulated_today)):
			run_daily_reminders()

		# 5. Assertions:
		# (a) New reminder log created for due_date = new_due_date and days_before = 7
		new_logs = frappe.get_all(
			"Tracora Reminder Log",
			filters={"reference_name": licence.name, "due_date": new_due_date, "days_before": 7}
		)
		self.assertGreaterEqual(len(new_logs), 1)

		# (b) Historical log for old due_date is untouched and did not cause suppression
		total_logs = frappe.db.count("Tracora Reminder Log", {"reference_name": licence.name})
		self.assertEqual(total_logs, len(logs) + len(new_logs))

	def test_idempotency_consecutive_runs(self):
		"""
		Idempotency: Running run_daily_reminders multiple times on identical state
		produces 0 duplicate emails or log entries.
		"""
		lic = self._create_licence(licence_expiry_date=add_days(today(), 7))
		run_daily_reminders()

		first_count = frappe.db.count("Tracora Reminder Log", {"reference_name": lic.name})
		self.assertGreaterEqual(first_count, 1)

		# Second consecutive run
		run_daily_reminders()
		second_count = frappe.db.count("Tracora Reminder Log", {"reference_name": lic.name})
		self.assertEqual(first_count, second_count)

	def test_fr90_scheduler_health_warning(self):
		"""
		FR-90: If last_reminder_run is older than 48 hours, health check returns
		is_stale = True with humanized message. Running the job clears it.
		"""
		settings = frappe.get_single("Tracora Settings")
		settings.last_reminder_run = add_days(now_datetime(), -3)
		settings.save(ignore_permissions=True)

		health = check_scheduler_health()
		self.assertTrue(health["is_stale"])
		self.assertGreaterEqual(health["days_ago"], 2)
		self.assertIn("3 days ago", health["stale_message"])

		# Running reminders updates last_reminder_run to now
		run_daily_reminders()

		health_after = check_scheduler_health()
		self.assertFalse(health_after["is_stale"])

	def test_nfr03_append_only_immutability(self):
		"""
		NFR-03: Tracora Reminder Log records cannot be edited or deleted by any user.
		"""
		lic = self._create_licence(licence_expiry_date=add_days(today(), 1))
		run_daily_reminders()

		log = frappe.get_last_doc("Tracora Reminder Log", filters={"reference_name": lic.name})
		self.assertIsNotNone(log)

		# Edit attempt -> ValidationError
		log.delivery_status = "Failed"
		self.assertRaises(frappe.ValidationError, log.save)

		# Delete attempt -> ValidationError
		self.assertRaises(frappe.ValidationError, log.delete)

	def test_role_and_enabled_filtering(self):
		"""
		Role & Enabled filtering:
		- Users without Tracora Admin/Super Admin role do not receive emails.
		- Disabled users (enabled = 0) do not receive emails.
		- When no active recipients exist, scheduler exits gracefully and flags health warning.
		"""
		# Create disabled admin
		disabled_email = "disabled_admin@example.com"
		if not frappe.db.exists("User", disabled_email):
			frappe.get_doc({
				"doctype": "User",
				"email": disabled_email,
				"first_name": "Disabled",
				"enabled": 0,
				"user_type": "System User",
				"roles": [{"role": "Tracora Admin"}],
			}).insert(ignore_permissions=True)
		else:
			frappe.db.set_value("User", disabled_email, "enabled", 0)

		recipients = get_active_recipients()
		self.assertNotIn(disabled_email, recipients)

		# Test empty recipients handling
		with patch("tracora.reminders.scheduler.get_active_recipients", return_value=[]):
			# Should not crash
			run_daily_reminders()
			health = check_scheduler_health()
			self.assertTrue(health["no_recipients"])
			self.assertIn("No active administrator users", health["recipient_message"])

	def test_settings_validation_reminder_lead_days(self):
		"""
		Tracora Settings validation: rejects malformed lead days at save time.
		"""
		# Invalid: negative numbers
		settings = frappe.get_single("Tracora Settings")
		settings.reminder_lead_days = "-1, 15, 7"
		self.assertRaises(frappe.ValidationError, settings.save)

		# Invalid: alphabetic / malformed text
		settings = frappe.get_single("Tracora Settings")
		settings.reminder_lead_days = "30, abc, 7"
		self.assertRaises(frappe.ValidationError, settings.save)

		# Valid: normalized properly
		settings = frappe.get_single("Tracora Settings")
		settings.reminder_lead_days = "30, 15, 7, 0"
		settings.save(ignore_permissions=True)
		self.assertEqual(settings.reminder_lead_days, "30,15,7,0")
