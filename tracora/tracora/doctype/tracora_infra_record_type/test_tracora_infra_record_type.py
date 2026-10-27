# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.patches.v1_0.seed_infra_record_types import execute as seed_types_execute
from tracora.patches.v1_0.seed_infra_categories import CATEGORIES
from tracora.tracora.doctype.tracora_infra_record_type.tracora_infra_record_type import FALLBACK_TYPE


class TestTracoraInfraRecordType(FrappeTestCase):
	def setUp(self):
		super().setUp()
		# Ensure base seeded types exist
		seed_types_execute()

	def test_22_empty_type_name_autoname_numbering(self):
		# Test 22: Type with empty type_name saves and is named "Untitled Type";
		# the second one becomes "Untitled Type 2"
		for name in ["Untitled Type", "Untitled Type 2", "Untitled Type 3"]:
			if frappe.db.exists("Tracora Infra Record Type", name):
				frappe.db.delete("Tracora Infra Record Type", {"name": name})

		t1 = frappe.get_doc({
			"doctype": "Tracora Infra Record Type",
			"type_name": ""
		}).insert()
		self.assertEqual(t1.name, "Untitled Type")

		t2 = frappe.get_doc({
			"doctype": "Tracora Infra Record Type",
			"type_name": "   "
		}).insert()
		self.assertEqual(t2.name, "Untitled Type 2")

		t2.delete()
		t1.delete()

	def test_23_duplicate_type_name_blocked(self):
		# Test 23: Duplicate type_name (different letter case) is blocked
		t1 = frappe.get_doc({
			"doctype": "Tracora Infra Record Type",
			"type_name": "Unique Test Cluster"
		}).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "Tracora Infra Record Type",
				"type_name": "  unique test cluster  "
			}).insert()

		t1.delete()

	def test_24_user_created_type_assigned_to_record(self):
		# Test 24: A user-created type can be assigned to a record and the record saves
		t = frappe.get_doc({
			"doctype": "Tracora Infra Record Type",
			"type_name": "Custom Storage Array"
		}).insert()

		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"record_type": t.name,
			"field_rows": [
				{"field_label": "Array Name", "field_value": "SAN-01"}
			]
		}).insert()

		self.assertEqual(rec.record_type, "Custom Storage Array")
		rec.reload()
		self.assertEqual(rec.record_type, "Custom Storage Array")

		rec.delete()
		t.delete()

	def test_25_record_saved_with_empty_record_type_gets_other(self):
		# Test 25: A record saved with an empty record_type gets "Other"
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"record_type": "",
			"field_rows": [
				{"field_label": "Hostname", "field_value": "node-empty-type"}
			]
		}).insert()

		self.assertEqual(rec.record_type, FALLBACK_TYPE)
		rec.reload()
		self.assertEqual(rec.record_type, FALLBACK_TYPE)

		rec.delete()

	def test_26_type_used_by_record_cannot_be_deleted(self):
		# Test 26: A type used by a record cannot be deleted (expect frappe.ValidationError);
		# the message includes the count
		t = frappe.get_doc({
			"doctype": "Tracora Infra Record Type",
			"type_name": "Deletable Protected By Record"
		}).insert()

		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"record_type": t.name,
			"field_rows": [
				{"field_label": "Device Name", "field_value": "Protected Host"}
			]
		}).insert()

		with self.assertRaises(frappe.ValidationError) as cm:
			t.delete()

		msg = str(cm.exception)
		self.assertIn("1 record(s)", msg)
		self.assertIn("0 category(ies)", msg)
		self.assertTrue(frappe.db.exists("Tracora Infra Record Type", t.name))

		rec.delete()
		t.delete()
		self.assertFalse(frappe.db.exists("Tracora Infra Record Type", t.name))

	def test_27_type_used_by_category_cannot_be_deleted(self):
		# Test 27: A type used by a category cannot be deleted
		t = frappe.get_doc({
			"doctype": "Tracora Infra Record Type",
			"type_name": "Deletable Protected By Cat"
		}).insert()

		cat = frappe.get_doc({
			"doctype": "Tracora Infra Category",
			"category_name": "Unique Test Category For Type Delete Guard",
			"record_type": t.name
		}).insert()

		with self.assertRaises(frappe.ValidationError) as cm:
			t.delete()

		msg = str(cm.exception)
		self.assertIn("1 category(ies)", msg)
		self.assertTrue(frappe.db.exists("Tracora Infra Record Type", t.name))

		cat.delete()
		t.delete()
		self.assertFalse(frappe.db.exists("Tracora Infra Record Type", t.name))

	def test_28_other_cannot_be_deleted(self):
		# Test 28: "Other" cannot be deleted even when nothing uses it
		other_doc = frappe.get_doc("Tracora Infra Record Type", FALLBACK_TYPE)
		with self.assertRaises(frappe.ValidationError) as cm:
			other_doc.delete()

		msg = str(cm.exception)
		self.assertIn("Other is the built-in fallback type and cannot be deleted", msg)
		self.assertTrue(frappe.db.exists("Tracora Infra Record Type", FALLBACK_TYPE))

	def test_29_admin_cannot_delete_super_admin_can(self):
		# Test 29: Tracora Admin cannot delete a type; Tracora Super Admin can (use a throwaway test type)
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

		can_super_delete = frappe.has_permission("Tracora Infra Record Type", "delete", user=super_admin_email)
		can_admin_delete = frappe.has_permission("Tracora Infra Record Type", "delete", user=admin_email)

		self.assertTrue(can_super_delete, "Tracora Super Admin must have delete permission")
		self.assertFalse(can_admin_delete, "Tracora Admin must NOT have delete permission")

		# Prove super admin can delete a throwaway type
		throwaway = frappe.get_doc({
			"doctype": "Tracora Infra Record Type",
			"type_name": "Throwaway Perm Type"
		}).insert()

		frappe.set_user(super_admin_email)
		try:
			throwaway.delete()
			self.assertFalse(frappe.db.exists("Tracora Infra Record Type", "Throwaway Perm Type"))
		finally:
			frappe.set_user("Administrator")

	def test_30_seed_patch_idempotence_and_no_overwrite(self):
		# Test 30: The seed patch run twice creates no duplicates and does not overwrite an edited icon
		seed_types_execute()

		count_before = frappe.db.count("Tracora Infra Record Type")

		# Edit icon of Vendor
		vendor_doc = frappe.get_doc("Tracora Infra Record Type", "Vendor")
		original_icon = vendor_doc.icon
		custom_icon = "custom-test-vendor-icon"
		vendor_doc.icon = custom_icon
		vendor_doc.save()

		# Run seed patch a second time
		seed_types_execute()

		count_after = frappe.db.count("Tracora Infra Record Type")
		self.assertEqual(count_before, count_after, "Seed patch must not create duplicate record types")

		vendor_doc.reload()
		self.assertEqual(vendor_doc.icon, custom_icon, "Seed patch must not overwrite user edits to record types")

		# Restore original icon
		vendor_doc.icon = original_icon
		vendor_doc.save()

	def test_31_category_seed_record_types_exist(self):
		# Test 31: Every record_type value used in the category seed list exists after the type seed runs
		for cat in CATEGORIES:
			rt = cat.get("record_type")
			self.assertTrue(
				frappe.db.exists("Tracora Infra Record Type", rt),
				f"Record Type '{rt}' required by Category '{cat['category_name']}' must exist"
			)

	def test_32_backfill_cleared_record_type_set_to_other(self):
		# Test 32: Backfill: a record whose record_type was cleared directly in the database is set to "Other" by the patch
		rec = frappe.get_doc({
			"doctype": "Tracora Infra Record",
			"field_rows": [
				{"field_label": "Test Field", "field_value": "Backfill Test Value"}
			]
		}).insert()

		# Clear record_type directly in the database
		frappe.db.sql(
			"UPDATE `tabTracora Infra Record` SET record_type = NULL WHERE name = %s",
			(rec.name,)
		)
		frappe.db.commit()

		cleared_val = frappe.db.get_value("Tracora Infra Record", rec.name, "record_type")
		self.assertFalse(cleared_val)

		# Run the patch
		seed_types_execute()
		frappe.db.commit()

		# Verify it was backfilled to "Other"
		backfilled_val = frappe.db.get_value("Tracora Infra Record", rec.name, "record_type")
		self.assertEqual(backfilled_val, FALLBACK_TYPE)

		rec.delete()
		frappe.db.commit()
