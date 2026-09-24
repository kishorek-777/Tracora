# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTracoraAssetCategory(FrappeTestCase):
	def test_category_creation_and_whitespace_strip(self):
		cat = frappe.get_doc({
			"doctype": "Tracora Asset Category",
			"category_name": "  Networking Equipment  "
		}).insert(ignore_if_duplicate=True)
		self.assertEqual(cat.category_name, "Networking Equipment")

	def test_empty_category_name_refused(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "Tracora Asset Category",
				"category_name": "   "
			}).insert()

	def test_disabled_toggle(self):
		cat = frappe.get_doc({
			"doctype": "Tracora Asset Category",
			"category_name": "Legacy Peripherals",
			"disabled": 1
		}).insert(ignore_if_duplicate=True)
		self.assertEqual(cat.disabled, 1)
