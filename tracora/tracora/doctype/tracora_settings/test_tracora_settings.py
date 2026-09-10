# Copyright (c) 2026, Kishore and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTracoraSettings(FrappeTestCase):
	def test_tracora_settings_defaults(self):
		settings = frappe.get_single("Tracora Settings")
		self.assertEqual(settings.tag_prefix, "TRC-")
		self.assertEqual(settings.reminder_lead_days, "30,15,7,2,1,0")
		self.assertEqual(float(settings.label_width_mm), 50.0)
		self.assertEqual(float(settings.label_height_mm), 25.0)
		self.assertEqual(float(settings.qr_size_mm), 15.0)

	def test_tracora_settings_read_write(self):
		settings = frappe.get_single("Tracora Settings")
		original_prefix = settings.tag_prefix

		try:
			settings.tag_prefix = "TEST-"
			settings.reminder_lead_days = "14,7,1"
			settings.label_width_mm = 60.0
			settings.label_height_mm = 30.0
			settings.qr_size_mm = 20.0
			settings.sender_email = "asset-alerts@example.com"
			settings.hrms_sync_enabled = 1
			settings.save()

			# Re-fetch from DB
			reloaded = frappe.get_single("Tracora Settings")
			self.assertEqual(reloaded.tag_prefix, "TEST-")
			self.assertEqual(reloaded.reminder_lead_days, "14,7,1")
			self.assertEqual(float(reloaded.label_width_mm), 60.0)
			self.assertEqual(float(reloaded.label_height_mm), 30.0)
			self.assertEqual(float(reloaded.qr_size_mm), 20.0)
			self.assertEqual(reloaded.sender_email, "asset-alerts@example.com")
			self.assertEqual(reloaded.hrms_sync_enabled, 1)
		finally:
			# Restore original values
			settings.tag_prefix = original_prefix
			settings.reminder_lead_days = "30,15,7,2,1,0"
			settings.label_width_mm = 50.0
			settings.label_height_mm = 25.0
			settings.qr_size_mm = 15.0
			settings.sender_email = None
			settings.hrms_sync_enabled = 0
			settings.save()

	def test_tracora_settings_permission_enforcement(self):
		# User with Tracora Admin role has read and write permission
		self.assertTrue(frappe.has_permission("Tracora Settings", "read", user="tracora_admin@test.local"))
		self.assertTrue(frappe.has_permission("Tracora Settings", "write", user="tracora_admin@test.local"))

		# User with only standard Guest / non-Tracora role does not have permission
		self.assertFalse(frappe.has_permission("Tracora Settings", "read", user="Guest"))
		self.assertFalse(frappe.has_permission("Tracora Settings", "write", user="Guest"))
