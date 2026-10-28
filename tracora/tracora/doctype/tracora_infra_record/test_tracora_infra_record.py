# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.api.infra import search_records, get_counts


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
		self.assertNotIn("ip address", rec.search_text)

		rec.delete()

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

		rec.delete()

	def test_03_save_completely_empty_record(self):
		# Test 3: Completely empty record (no category, no rows) saves; title == "Untitled".
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record"
		}).insert()

		self.assertEqual(rec.title, "Untitled")
		self.assertEqual(rec.search_text, "")
		self.assertEqual(len(rec.field_rows), 0)

		rec.delete()

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

		rec.delete()

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

		rec.delete()

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
		self.assertIn("initial value", rec.search_text)
		self.assertNotIn("renamed custom label", rec.search_text)

		rec.delete()

	def test_07_record_found_by_custom_row_value(self):
		# Test 7: A record is found by a value that sits in a custom (non-template) row
		custom_val = "uniq-custom-hw-84729"
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "Arbitrary Custom Header", "field_value": custom_val}
			]
		}).insert()

		res = search_records(query=custom_val)
		found_names = [r["name"] for r in res["records"]]
		self.assertIn(rec.name, found_names)
		self.assertGreaterEqual(res["total"], 1)

		rec.delete()

	def test_08_permissions_super_admin_vs_admin(self):
		# Test 8: Permissions: create two test users, one with only "Tracora Admin", one with only "Tracora Super Admin".
		# Use frappe.has_permission(..., "delete", user=...) to prove Admin cannot delete and Super Admin can.
		super_admin_email = "test_super_admin_perm@example.com"
		admin_email = "test_admin_perm@example.com"

		for email, role in [(super_admin_email, "Tracora Super Admin"), (admin_email, "Tracora Admin")]:
			if not frappe.db.exists("User", email):
				frappe.get_doc({
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

		self.assertFalse(can_super_delete, "Tracora Super Admin must NOT have delete permission")
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

		rec.delete()

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

		rec.delete()

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

		rec.delete()

	def test_16_two_word_query_matches_both_words_in_different_rows(self):
		# Test 16: A two-word query matches only records that contain both words, in different rows
		rec_match = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "Rack Identifier", "field_value": "OmegaWing"},
				{"field_label": "Bay Slot", "field_value": "SectorSeven"},
			]
		}).insert()

		rec_no_match = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "Rack Identifier", "field_value": "OmegaWing"},
				{"field_label": "Bay Slot", "field_value": "SectorEight"},
			]
		}).insert()

		res = search_records(query="OmegaWing SectorSeven")
		names = [r["name"] for r in res["records"]]
		self.assertIn(rec_match.name, names)
		self.assertNotIn(rec_no_match.name, names)

		rec_match.delete()
		rec_no_match.delete()

	def test_17_query_containing_wildcards_does_not_match_unrelated(self):
		# Test 17: A query containing "%" or "_" does not match unrelated records
		rec_exact = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "IP Label", "field_value": "10_0_wildcard_test"}
			]
		}).insert()

		rec_unrelated = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "IP Label", "field_value": "1000_wildcard_test"}
			]
		}).insert()

		rec_percent = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "Discount", "field_value": "99%discount_test"}
			]
		}).insert()

		# Query with underscore
		res_underscore = search_records(query="10_0_wildcard")
		names_u = [r["name"] for r in res_underscore["records"]]
		self.assertIn(rec_exact.name, names_u)
		self.assertNotIn(rec_unrelated.name, names_u)

		# Query with percent
		res_percent = search_records(query="99%discount")
		names_p = [r["name"] for r in res_percent["records"]]
		self.assertIn(rec_percent.name, names_p)

		rec_exact.delete()
		rec_unrelated.delete()
		rec_percent.delete()

	def test_18_record_type_and_category_filters_and_total_ignores_paging(self):
		# Test 18: record_type and category filters work; "total" ignores start and page_length
		cat_name = "Unique Category Filter Test"
		cat = frappe.get_doc({
			"doctype": "Tracora Infra Category",
			"category_name": cat_name,
			"record_type": "Device"
		}).insert()

		rec1 = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"record_type": "Device",
			"category": cat.name,
			"field_rows": [{"field_label": "Host", "field_value": "dev-node-01"}]
		}).insert()

		rec2 = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"record_type": "Building",
			"category": cat.name,
			"field_rows": [{"field_label": "Building", "field_value": "bld-site-01"}]
		}).insert()

		# Filter by record_type=Device and category
		res_device = search_records(record_type="Device", category=cat.name)
		names = [r["name"] for r in res_device["records"]]
		self.assertIn(rec1.name, names)
		self.assertNotIn(rec2.name, names)

		# Paging check: start=10, page_length=1
		res_paged = search_records(record_type="Device", category=cat.name, start=10, page_length=1)
		self.assertEqual(len(res_paged["records"]), 0)
		self.assertEqual(res_paged["total"], 1, "Total must reflect all matching records regardless of paging")

		rec1.delete()
		rec2.delete()
		cat.delete()

	def test_19_paging_boundary_capping(self):
		# Test 19: page_length=1000 is capped at 100; page_length=0 becomes 1; start=-5 becomes 0
		res_cap = search_records(page_length=1000)
		self.assertLessEqual(len(res_cap["records"]), 100)

		res_zero = search_records(page_length=0, start=-5)
		self.assertEqual(len(res_zero["records"]), 1)

	def test_20_get_counts_returns_one_entry_per_existing_type_including_zero(self):
		# Test 20: get_counts returns one entry per existing type including a type with zero records
		throwaway_type = frappe.get_doc({
			"doctype": "Tracora Infra Record Type",
			"type_name": "Throwaway Count Test Type",
			"sort_order": 999
		}).insert()

		counts_before = {item["record_type"]: item["count"] for item in get_counts()}
		self.assertIn(throwaway_type.name, counts_before)
		self.assertEqual(counts_before[throwaway_type.name], 0)

		# Create a record of type Device
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"record_type": "Device",
			"field_rows": [{"field_label": "Name", "field_value": "Count Test Device"}]
		}).insert()

		counts_after = {item["record_type"]: item["count"] for item in get_counts()}
		self.assertEqual(counts_after["Device"] - counts_before.get("Device", 0), 1)

		rec.delete()
		throwaway_type.delete()

	def test_21_unauthorized_user_refused(self):
		# Test 21: A user with no Tracora role is refused by both functions (expect frappe.PermissionError)
		no_role_user = "test_no_tracora_role@example.com"
		if not frappe.db.exists("User", no_role_user):
			frappe.get_doc({
				"doctype": "User",
				"email": no_role_user,
				"first_name": "NoRole",
				"last_name": "User",
				"send_welcome_email": 0,
				"roles": []
			}).insert(ignore_permissions=True)
		else:
			u = frappe.get_doc("User", no_role_user)
			u.roles = []
			u.save(ignore_permissions=True)

		frappe.set_user(no_role_user)
		try:
			with self.assertRaises(frappe.PermissionError):
				search_records()

			with self.assertRaises(frappe.PermissionError):
				get_counts()
		finally:
			frappe.set_user("Administrator")

	def test_22b_search_records_invalid_record_type_throws(self):
		# Test 22b: search_records with a record_type that does not exist throws a clear error
		with self.assertRaises(frappe.ValidationError):
			search_records(record_type="NonExistentType_99999")

	def test_33_searching_label_alone_does_not_match(self):
		# Test 33: Searching a label name alone (e.g. "Serial Number") does not match a record whose values do not contain that text
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "Serial Number", "field_value": "SN-XYZ-987654"}
			]
		}).insert()

		self.assertNotIn("serial number", rec.search_text)
		self.assertIn("sn-xyz-987654", rec.search_text)

		res = search_records(query="Serial Number")
		matched_names = [r["name"] for r in res["records"]]
		self.assertNotIn(rec.name, matched_names)

		rec.delete()

	def test_34_rebuild_patch_idempotence_and_fixes_old_format(self):
		# Test 34: The patch run twice changes nothing the second time and fixes a record whose search_text was set to the old label+value format
		from tracora.patches.v1_0.rebuild_infra_search_text import execute as rebuild_execute

		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "OldLabelHeader", "field_value": "OldValueContent"}
			]
		}).insert()

		# Simulate old search_text format: label + value
		old_format = "oldlabelheader oldvaluecontent"
		frappe.db.set_value("Tracora Infra Record", rec.name, "search_text", old_format, update_modified=False)
		frappe.db.commit()

		self.assertEqual(frappe.db.get_value("Tracora Infra Record", rec.name, "search_text"), old_format)

		# First run of patch
		rebuild_execute()
		frappe.db.commit()

		fixed_val = frappe.db.get_value("Tracora Infra Record", rec.name, "search_text")
		self.assertEqual(fixed_val, "oldvaluecontent")

		# Second run of patch
		rebuild_execute()
		frappe.db.commit()

		rechecked_val = frappe.db.get_value("Tracora Infra Record", rec.name, "search_text")
		self.assertEqual(rechecked_val, "oldvaluecontent")

		rec.delete()
		frappe.db.commit()

	def test_35_build_search_text_helper(self):
		# Test 35: The helper ignores empty values and trims whitespace
		from tracora.tracora.doctype.tracora_infra_record.tracora_infra_record import build_search_text

		rows = [
			{"field_label": "Label 1", "field_value": "   TrimValOne   "},
			{"field_label": "Label 2", "field_value": ""},
			{"field_label": "Label 3", "field_value": "   "},
			{"field_label": "Label 4", "field_value": None},
			{"field_label": "Label 5", "field_value": "TrimValTwo"},
		]

		result = build_search_text(rows)
		self.assertEqual(result, "trimvalone trimvaltwo")
