# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTracoraInfraRecord(FrappeTestCase):
	def setUp(self):
		super().setUp()

	def test_01_save_record_with_single_row(self):
		# Test 1: Record with ONLY one row (label "IP Address", value "10.0.0.1") saves; title == "10.0.0.1".
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "IP Address", "field_value": "10.0.0.1"}
			]
		}).insert()

		self.assertTrue(rec.name.startswith("INF-"))
		self.assertEqual(rec.title, "10.0.0.1")
		self.assertIn("10.0.0.1", rec.search_text)
		self.assertIn("ip address", rec.search_text)

	def test_02_save_record_with_device_name_row(self):
		# Test 2: Record with ONLY a device name row saves.
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "Device Name", "field_value": "Core-Router-Alpha"}
			]
		}).insert()

		self.assertEqual(rec.title, "Core-Router-Alpha")
		self.assertIn("core-router-alpha", rec.search_text)

	def test_03_save_completely_empty_record(self):
		# Test 3: Completely empty record (no category, no rows) saves; title == "Untitled".
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record"
		}).insert()

		self.assertEqual(rec.title, "Untitled")
		self.assertEqual(rec.search_text, "")
		self.assertEqual(len(rec.field_rows), 0)

	def test_04_row_with_empty_label_and_value(self):
		# Test 4: Row with empty label and a value -> label becomes "Untitled Field".
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "  ", "field_value": "192.168.1.254"}
			]
		}).insert()

		self.assertEqual(len(rec.field_rows), 1)
		self.assertEqual(rec.field_rows[0].field_label, "Untitled Field")
		self.assertEqual(rec.field_rows[0].field_value, "192.168.1.254")
		self.assertEqual(rec.title, "192.168.1.254")

	def test_05_row_with_empty_label_and_empty_value_removed(self):
		# Test 5: Row with empty label and empty value -> removed.
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "", "field_value": ""},
				{"field_label": "   ", "field_value": "   "},
				{"field_label": "Hostname", "field_value": "srv-db-01"}
			]
		}).insert()

		self.assertEqual(len(rec.field_rows), 1)
		self.assertEqual(rec.field_rows[0].field_label, "Hostname")
		self.assertEqual(rec.field_rows[0].field_value, "srv-db-01")
		self.assertEqual(rec.field_rows[0].idx, 1)
		self.assertEqual(rec.title, "srv-db-01")

	def test_06_rename_label_persists_without_migrate(self):
		# Test 6: Rename a label on a saved record and save again -> persists, no migrate needed.
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "Initial Label", "field_value": "Initial Value"}
			]
		}).insert()

		rec.field_rows[0].field_label = "Renamed Custom Label"
		rec.save()

		rec.reload()
		self.assertEqual(rec.field_rows[0].field_label, "Renamed Custom Label")
		self.assertIn("renamed custom label", rec.search_text)

	def test_08_permissions_super_admin_vs_admin(self):
		# Test 8: Permissions: create two test users, one with only "Tracora Admin", one with only "Tracora Super Admin".
		# Use frappe.has_permission(..., "delete", user=...) to prove Admin cannot delete and Super Admin can.
		super_admin_email = "test_super_admin_perm@example.com"
		admin_email = "test_admin_perm@example.com"

		for email, role in [(super_admin_email, "Tracora Super Admin"), (admin_email, "Tracora Admin")]:
			if not frappe.db.exists("User", email):
				u = frappe.get_doc({
					"doctype": "User",
					"email": email,
					"first_name": "Test",
					"last_name": role,
					"send_welcome_email": 0,
					"roles": [{"role": role}]
				}).insert(ignore_permissions=True)
			else:
				u = frappe.get_doc("User", email)
				u.roles = []
				u.append("roles", {"role": role})
				u.save(ignore_permissions=True)

		# Check delete permission on DocType
		can_super_delete = frappe.has_permission("Tracora Infra Record", "delete", user=super_admin_email)
		can_admin_delete = frappe.has_permission("Tracora Infra Record", "delete", user=admin_email)

		self.assertTrue(can_super_delete, "Tracora Super Admin must have delete permission")
		self.assertFalse(can_admin_delete, "Tracora Admin must NOT have delete permission")

		# Check write/read permissions
		self.assertTrue(frappe.has_permission("Tracora Infra Record", "read", user=admin_email))
		self.assertTrue(frappe.has_permission("Tracora Infra Record", "write", user=admin_email))

	def test_13_first_value_300_chars_saves_and_title_cut_to_140(self):
		# Test 13: A record whose first value is 300 characters long saves.
		long_val = "A" * 300
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "Description", "field_value": long_val}
			]
		}).insert()

		self.assertEqual(len(rec.title), 140)
		self.assertEqual(rec.title, "A" * 140)
		self.assertEqual(rec.field_rows[0].field_value, long_val)

	def test_14_row_with_200_char_label_saves_and_cut_to_140(self):
		# Test 14: A row with a 200-character label saves.
		long_label = "B" * 200
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": long_label, "field_value": "Short Value"}
			]
		}).insert()

		self.assertEqual(len(rec.field_rows[0].field_label), 140)
		self.assertEqual(rec.field_rows[0].field_label, "B" * 140)

	def test_15_multiline_value_title_uses_only_first_line(self):
		# Test 15: A value containing a line break: title uses only the first line.
		multiline_val = "First Line Of Name\nSecond Line Details\nThird Line Notes"
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "Device Name", "field_value": multiline_val}
			]
		}).insert()

		self.assertEqual(rec.title, "First Line Of Name")
		self.assertEqual(rec.field_rows[0].field_value, multiline_val)
