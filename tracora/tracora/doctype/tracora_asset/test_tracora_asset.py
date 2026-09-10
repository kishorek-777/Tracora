# Copyright (c) 2026, Kishore and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTracoraAsset(FrappeTestCase):
	def setUp(self):
		super().setUp()
		# Base internal company
		if not frappe.db.exists("Tracora Company", "Test Internal Corp"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Test Internal Corp",
				"company_type": "Internal",
				"company_abbr": "TIC",
				"company_address": "123 Internal St, Chennai",
				"source": "Tracora"
			}).insert()

		# Base external company
		if not frappe.db.exists("Tracora Company", "Test External Agency"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Test External Agency",
				"company_type": "External",
				"company_abbr": "TEA",
				"company_address": "456 External Rd, Bangalore",
				"source": "Tracora"
			}).insert()

		# Base branch
		if not frappe.db.exists("Tracora Branch", "HQ - TIC"):
			frappe.get_doc({
				"doctype": "Tracora Branch",
				"branch_name": "HQ",
				"company": "Test Internal Corp",
				"source": "Tracora"
			}).insert()

		# Base branch 2
		if not frappe.db.exists("Tracora Branch", "North - TIC"):
			frappe.get_doc({
				"doctype": "Tracora Branch",
				"branch_name": "North",
				"company": "Test Internal Corp",
				"source": "Tracora"
			}).insert()

		# Base department
		if not frappe.db.exists("Tracora Department", "IT - TIC"):
			frappe.get_doc({
				"doctype": "Tracora Department",
				"department_name": "IT",
				"company": "Test Internal Corp",
				"source": "Tracora"
			}).insert()

		# Base location
		if not frappe.db.exists("Tracora Location", "Server Room 1"):
			frappe.get_doc({
				"doctype": "Tracora Location",
				"location_name": "Server Room 1",
				"address": "Floor 2, HQ Building, Chennai",
				"latitude": 13.0827,
				"longitude": 80.2707
			}).insert()

		# Active employee
		if not frappe.db.exists("Tracora Employee", "EMP-ACT-001"):
			frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_code": "EMP-ACT-001",
				"employee_name": "Active Tech",
				"mobile": "9876543210",
				"company": "Test Internal Corp",
				"branch": "HQ - TIC",
				"department": "IT - TIC",
				"status": "Active",
				"source": "Tracora"
			}).insert()

		# Exited employee
		if not frappe.db.exists("Tracora Employee", "EMP-EXT-001"):
			frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_code": "EMP-EXT-001",
				"employee_name": "Former Staff",
				"mobile": "9876543211",
				"company": "Test Internal Corp",
				"branch": "HQ - TIC",
				"department": "IT - TIC",
				"status": "Exited",
				"source": "Tracora"
			}).insert()

	def test_separate_owner_and_holding_company_fr12(self):
		"""FR-12: Asset saved with separate owner and holding company."""
		asset = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Client Loaner Laptop",
			"brand": "Dell",
			"model_number": "Latitude 5420",
			"serial_no": "DL-SEP-OWN-001",
			"owner_company": "Test External Agency",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		}).insert()

		self.assertTrue(asset.name.startswith("TRC-"))
		self.assertEqual(asset.owner_company, "Test External Agency")
		self.assertEqual(asset.holding_company, "Test Internal Corp")

	def test_cross_field_uniqueness_and_brand_isolation_fr13(self):
		"""FR-13: Serial unique per brand; Tag and Serial share namespace."""
		# 1. Asset A with serial ABC123 saves
		asset_a = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Asset A",
			"brand": "Dell",
			"serial_no": "ABC123_UNIQUE",
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		}).insert()
		self.assertTrue(asset_a.name)

		# 2. Asset B with manual tag matching Asset A's serial is refused
		asset_b = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Manual entry",
			"asset_tag": "ABC123_UNIQUE",
			"asset_name": "Asset B",
			"brand": "Lenovo",
			"serial_no": "LEN-001",
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		})
		with self.assertRaises(frappe.ValidationError) as cm:
			asset_b.insert()
		self.assertIn("Tag and serial share one namespace", str(cm.exception))

		# 3. Asset with candidate serial matching an existing tag is refused
		asset_c_tag = asset_a.asset_tag
		asset_c = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Asset C",
			"brand": "Lenovo",
			"serial_no": asset_c_tag,
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		})
		with self.assertRaises(frappe.ValidationError) as cm:
			asset_c.insert()
		self.assertIn("Tag and serial share one namespace", str(cm.exception))

		# 4. Same serial under different brands both save
		shared_serial = "MULTI-BRAND-SER-1"
		asset_dell = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Dell Multi",
			"brand": "Dell",
			"serial_no": shared_serial,
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		}).insert()

		asset_hp = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "HP Multi",
			"brand": "HP",
			"serial_no": shared_serial,
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		}).insert()

		self.assertTrue(asset_dell.name)
		self.assertTrue(asset_hp.name)
		self.assertEqual(asset_dell.serial_no, asset_hp.serial_no)

		# Duplicate serial under the SAME brand is refused
		asset_dell_dup = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Dell Dup",
			"brand": "Dell",
			"serial_no": shared_serial,
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		})
		with self.assertRaises(frappe.DuplicateEntryError) as cm:
			asset_dell_dup.insert()
		self.assertIn("already exists for brand 'Dell'", str(cm.exception))

	def test_brand_edit_revalidates_serial_uniqueness(self):
		"""Brand change on an existing asset re-validates serial uniqueness against the NEW brand."""
		common_serial = "BRAND-SWITCH-SN-01"
		# Asset 1: Brand HP
		asset_hp = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "HP Asset",
			"brand": "HP",
			"serial_no": common_serial,
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		}).insert()

		# Asset 2: Brand Dell with same serial (valid across different brands)
		asset_dell = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Dell Asset",
			"brand": "Dell",
			"serial_no": common_serial,
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		}).insert()

		# Now edit Asset 2's brand to 'HP' -> must clash with Asset 1 and fail!
		asset_dell.brand = "HP"
		with self.assertRaises(frappe.DuplicateEntryError) as cm:
			asset_dell.save()
		self.assertIn("already exists for brand 'HP'", str(cm.exception))

	def test_reserved_prefix_refusal_for_manual_tags(self):
		"""FR-66, FR-67: Manual tag starting with reserved prefix TRC- is refused."""
		asset = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Manual entry",
			"asset_tag": "TRC-999999",
			"asset_name": "Reserved Tag Attempt",
			"brand": "Dell",
			"serial_no": "SN-RES-01",
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		})
		with self.assertRaises(frappe.ValidationError) as cm:
			asset.insert()
		self.assertIn("reserved prefix", str(cm.exception))

	def test_independent_status_and_condition_fr14_fr15(self):
		"""FR-14, FR-15: Asset simultaneously In Store and Poor."""
		asset = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Old Monitor",
			"brand": "Samsung",
			"serial_no": "SAM-POOR-001",
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Poor"
		}).insert()
		self.assertEqual(asset.status, "In Store")
		self.assertEqual(asset.condition, "Poor")

	def test_missing_location_refused_fr05(self):
		"""FR-05: Asset save with no location is refused."""
		asset = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "No Loc Device",
			"brand": "Cisco",
			"serial_no": "CSC-001",
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "",
			"status": "In Store",
			"condition": "Good"
		})
		with self.assertRaises(frappe.ValidationError) as cm:
			asset.insert()
		self.assertIn("Location is required", str(cm.exception))

	def test_conditional_branch_requirement_fr72(self):
		"""FR-72: Internal holding company requires branch; External does not."""
		# Internal with no branch -> refused
		asset_int = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Internal No Branch",
			"brand": "Apple",
			"serial_no": "APL-NOBR-01",
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": None,
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		})
		with self.assertRaises(frappe.ValidationError) as cm:
			asset_int.insert()
		self.assertIn("Branch is required when holding company", str(cm.exception))

		# External with no branch -> saves
		asset_ext = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "External No Branch",
			"brand": "Apple",
			"serial_no": "APL-EXT-01",
			"owner_company": "Test External Agency",
			"holding_company": "Test External Agency",
			"branch": None,
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		}).insert()
		self.assertTrue(asset_ext.name)
		self.assertIsNone(asset_ext.branch)

	def test_shared_equipment_and_poc_fr93(self):
		"""FR-93: is_shared blocks individual assignment; point_of_contact validation."""
		# 1. Saving an asset with is_shared=1 and assigned_to is refused
		asset_bad = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Shared Printer",
			"brand": "HP",
			"serial_no": "HP-PRN-001",
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good",
			"is_shared": 1,
			"assigned_to": "EMP-ACT-001"
		})
		with self.assertRaises(frappe.ValidationError) as cm:
			asset_bad.insert()
		self.assertIn("marked as shared equipment and cannot be assigned to an individual", str(cm.exception))

		# 2. Shared asset saves with active POC
		asset_shared = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Floor Router",
			"brand": "MikroTik",
			"serial_no": "MTK-RTR-001",
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "North - TIC",  # North branch
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good",
			"is_shared": 1,
			"point_of_contact": "EMP-ACT-001"  # Belongs to HQ branch (cross-branch POC allowed!)
		}).insert()
		self.assertEqual(asset_shared.is_shared, 1)
		self.assertEqual(asset_shared.point_of_contact, "EMP-ACT-001")

		# 3. Setting POC to an Exited employee is refused
		asset_exited_poc = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Meeting Room TV",
			"brand": "Sony",
			"serial_no": "SNY-TV-001",
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good",
			"is_shared": 1,
			"point_of_contact": "EMP-EXT-001"  # Status is Exited
		})
		with self.assertRaises(frappe.ValidationError) as cm:
			asset_exited_poc.insert()
		self.assertIn("has status 'Exited'", str(cm.exception))

	def test_delete_permission_enforcement_fr19(self):
		"""FR-19: Admin cannot delete; Super Admin can delete."""
		asset = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Delete Test Asset",
			"brand": "Dell",
			"serial_no": "DEL-DEL-001",
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Server Room 1",
			"status": "In Store",
			"condition": "Good"
		}).insert()

		# Test as Tracora Admin (delete: 0 in permissions)
		frappe.set_user("Administrator")
		admin_user = "test_tracora_admin@example.com"
		if not frappe.db.exists("User", admin_user):
			user_doc = frappe.get_doc({
				"doctype": "User",
				"email": admin_user,
				"first_name": "Test",
				"last_name": "Admin",
				"roles": [{"role": "Tracora Admin"}]
			}).insert(ignore_permissions=True)

		frappe.set_user(admin_user)
		self.assertFalse(asset.has_permission("delete"))

		# Super Admin user (delete: 1 in permissions)
		frappe.set_user("Administrator")
		super_admin_user = "test_super_admin@example.com"
		if not frappe.db.exists("User", super_admin_user):
			frappe.get_doc({
				"doctype": "User",
				"email": super_admin_user,
				"first_name": "Super",
				"last_name": "Admin",
				"roles": [{"role": "Tracora Super Admin"}]
			}).insert(ignore_permissions=True)

		frappe.set_user(super_admin_user)
		self.assertTrue(asset.has_permission("delete"))
		frappe.set_user("Administrator")
