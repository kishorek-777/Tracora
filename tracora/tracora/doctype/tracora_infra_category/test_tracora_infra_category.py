# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.patches.v1_0.seed_infra_categories import execute as seed_execute


class TestTracoraInfraCategory(FrappeTestCase):
	def setUp(self):
		super().setUp()

	def test_09_deleting_category_used_by_record_is_blocked(self):
		# Test 9: Deleting a category used by a record is blocked (expect frappe.ValidationError).
		cat = frappe.get_doc({
			"doctype": "Tracora Infra Category",
			"category_name": "Unique Test Cat For Delete Guard"
		}).insert()

		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"category": cat.name,
			"field_rows": [
				{"field_label": "Device Name", "field_value": "Protected Device"}
			]
		}).insert()

		with self.assertRaises(frappe.ValidationError):
			cat.delete()

		# Verify it was not deleted
		self.assertTrue(frappe.db.exists("Tracora Infra Category", cat.name))

		# Cleanup record then delete category successfully
		rec.delete()
		cat.delete()
		self.assertFalse(frappe.db.exists("Tracora Infra Category", cat.name))

	def test_10_seed_patch_idempotence_and_no_overwrite(self):
		# Test 10: Run the seed patch execute() twice: no duplicate categories,
		# and a template field you edited between runs is NOT overwritten.
		seed_execute()

		# Count categories
		count_before = frappe.db.count("Tracora Infra Category")

		# Edit a seeded category template field
		target_cat_name = "Internet / ISP"
		doc = frappe.get_doc("Tracora Infra Category", target_cat_name)
		original_labels = [f.field_label for f in doc.template_fields]
		custom_label = "Custom Test Bandwidth Field"

		if custom_label not in original_labels:
			doc.append("template_fields", {"field_label": custom_label})
			doc.save()

		# Run seed patch a second time
		seed_execute()

		count_after = frappe.db.count("Tracora Infra Category")
		self.assertEqual(count_before, count_after, "Seed patch must not create duplicate categories")

		doc.reload()
		reloaded_labels = [f.field_label for f in doc.template_fields]
		self.assertIn(custom_label, reloaded_labels, "Seed patch must not overwrite user edits to categories")

	def test_11_autoname_untitled_category_numbering(self):
		# Test 11: A category with empty category_name saves and is named "Untitled Category";
		# a second one becomes "Untitled Category 2".
		# Clean any prior Untitled Category docs
		for name in ["Untitled Category", "Untitled Category 2", "Untitled Category 3"]:
			if frappe.db.exists("Tracora Infra Category", name):
				frappe.db.delete("Tracora Infra Category Field", {"parent": name})
				frappe.db.delete("Tracora Infra Category", {"name": name})

		c1 = frappe.get_doc({
			"doctype": "Tracora Infra Category",
			"category_name": ""
		}).insert()
		self.assertEqual(c1.name, "Untitled Category")

		c2 = frappe.get_doc({
			"doctype": "Tracora Infra Category",
			"category_name": "   "
		}).insert()
		self.assertEqual(c2.name, "Untitled Category 2")

		# Cleanup
		c2.delete()
		c1.delete()

	def test_12_duplicate_category_name_blocked(self):
		# Additional validation check: case-insensitive duplicate category_name blocked
		c1 = frappe.get_doc({
			"doctype": "Tracora Infra Category",
			"category_name": "Unique Router Matrix"
		}).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "Tracora Infra Category",
				"category_name": "  unique router matrix  "
			}).insert()

		c1.delete()
