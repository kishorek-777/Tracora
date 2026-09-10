# Copyright (c) 2026, Kishore and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTracoraMasters(FrappeTestCase):
	def setUp(self):
		super().setUp()
		# Setup base internal and external companies
		if not frappe.db.exists("Tracora Company", "Test Internal Corp"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Test Internal Corp",
				"company_type": "Internal",
				"company_abbr": "TIC",
				"company_address": "123 Internal St, Chennai",
				"source": "Tracora"
			}).insert()

		if not frappe.db.exists("Tracora Company", "Test External Agency"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Test External Agency",
				"company_type": "External",
				"company_abbr": "TEA",
				"company_address": "456 External Rd, Bangalore",
				"source": "Tracora"
			}).insert()

	def test_company_creation_without_hrms_fr01(self):
		"""FR-01: Company created with no HRMS record behind it."""
		company_name = "Standalone Company Inc"
		if frappe.db.exists("Tracora Company", company_name):
			frappe.delete_doc("Tracora Company", company_name, force=1)

		doc = frappe.get_doc({
			"doctype": "Tracora Company",
			"company_name": company_name,
			"company_type": "Internal",
			"company_abbr": "SCI",
			"company_address": "789 Standalone Blvd",
			"source": "Tracora"
		}).insert()

		self.assertEqual(doc.name, company_name)
		self.assertEqual(doc.source, "Tracora")
		self.assertIsNone(doc.hrms_company)

	def test_company_without_type_refused_fr70(self):
		"""FR-70: Company type must be chosen; no default."""
		doc = frappe.new_doc("Tracora Company")
		doc.company_name = "Missing Type Ltd"
		doc.company_abbr = "MTL"
		doc.company_address = "Address"
		doc.company_type = None

		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_duplicate_company_abbr_refused(self):
		"""Rule 7: Company abbreviation unique index."""
		company_a = "Company Alpha"
		company_b = "Company Beta"
		if frappe.db.exists("Tracora Company", company_a):
			frappe.delete_doc("Tracora Company", company_a, force=1)
		if frappe.db.exists("Tracora Company", company_b):
			frappe.delete_doc("Tracora Company", company_b, force=1)

		frappe.get_doc({
			"doctype": "Tracora Company",
			"company_name": company_a,
			"company_type": "Internal",
			"company_abbr": "CABR",
			"company_address": "Addr A"
		}).insert()

		doc_b = frappe.get_doc({
			"doctype": "Tracora Company",
			"company_name": company_b,
			"company_type": "External",
			"company_abbr": "CABR",
			"company_address": "Addr B"
		})
		with self.assertRaises((frappe.DuplicateEntryError, frappe.ValidationError)):
			doc_b.insert()

	def test_branch_and_department_autoname_and_collisions(self):
		"""Rule 7: Branch and Department named {name} - {company_abbr}."""
		# Create two branches named Chennai under two different companies
		if frappe.db.exists("Tracora Branch", "Chennai - TIC"):
			frappe.delete_doc("Tracora Branch", "Chennai - TIC", force=1)
		if frappe.db.exists("Tracora Branch", "Chennai - TEA"):
			frappe.delete_doc("Tracora Branch", "Chennai - TEA", force=1)

		b1 = frappe.get_doc({
			"doctype": "Tracora Branch",
			"branch_name": "Chennai",
			"company": "Test Internal Corp"
		}).insert()

		b2 = frappe.get_doc({
			"doctype": "Tracora Branch",
			"branch_name": "Chennai",
			"company": "Test External Agency"
		}).insert()

		self.assertEqual(b1.name, "Chennai - TIC")
		self.assertEqual(b2.name, "Chennai - TEA")

		# Attempt duplicate Chennai under TIC
		b_dup = frappe.get_doc({
			"doctype": "Tracora Branch",
			"branch_name": "Chennai",
			"company": "Test Internal Corp"
		})
		with self.assertRaises(frappe.DuplicateEntryError):
			b_dup.insert()

		# Same for department
		if frappe.db.exists("Tracora Department", "Operations - TIC"):
			frappe.delete_doc("Tracora Department", "Operations - TIC", force=1)

		d1 = frappe.get_doc({
			"doctype": "Tracora Department",
			"department_name": "Operations",
			"company": "Test Internal Corp"
		}).insert()
		self.assertEqual(d1.name, "Operations - TIC")

		d_dup = frappe.get_doc({
			"doctype": "Tracora Department",
			"department_name": "Operations",
			"company": "Test Internal Corp"
		})
		with self.assertRaises(frappe.DuplicateEntryError):
			d_dup.insert()

	def test_location_coordinates_and_virtual_map_url_fr03_04(self):
		"""FR-03, FR-04: Location coordinate validation and virtual map_url."""
		loc_name = "HQ Tower Chennai"
		if frappe.db.exists("Tracora Location", loc_name):
			frappe.delete_doc("Tracora Location", loc_name, force=1)

		loc = frappe.get_doc({
			"doctype": "Tracora Location",
			"location_name": loc_name,
			"address": "OMR Tech Corridor, Chennai",
			"latitude": 13.082700,
			"longitude": 80.270700
		}).insert()

		self.assertEqual(loc.map_url, "https://www.google.com/maps?q=13.0827,80.2707")

		# Change coordinates and check link update
		loc.latitude = 12.971600
		loc.longitude = 77.594600
		loc.save()
		self.assertEqual(loc.map_url, "https://www.google.com/maps?q=12.9716,77.5946")

		# Invalid latitude > 90
		loc_invalid = frappe.get_doc({
			"doctype": "Tracora Location",
			"location_name": "Invalid Lat Place",
			"address": "Invalid",
			"latitude": 95.0,
			"longitude": 80.0
		})
		with self.assertRaises(frappe.ValidationError):
			loc_invalid.insert()

		# Invalid longitude > 180
		loc_invalid_lon = frappe.get_doc({
			"doctype": "Tracora Location",
			"location_name": "Invalid Lon Place",
			"address": "Invalid",
			"latitude": 10.0,
			"longitude": 200.0
		})
		with self.assertRaises(frappe.ValidationError):
			loc_invalid_lon.insert()

	def test_external_employee_autoname_and_override_protection_fr92(self):
		"""FR-92: External employee gets EXT-.###### autoname, immune to manual override."""
		emp = frappe.get_doc({
			"doctype": "Tracora Employee",
			"company": "Test External Agency",
			"employee_name": "Vendor Tech Support",
			"mobile": "9888877777"
		}).insert()

		self.assertTrue(emp.name.startswith("EXT-"))
		self.assertEqual(emp.employee_code, emp.name)

		# Attempt manual code override
		emp_override = frappe.get_doc({
			"doctype": "Tracora Employee",
			"company": "Test External Agency",
			"employee_code": "MANUAL-OVERRIDE-CODE",
			"employee_name": "Vendor Tech Support 2",
			"mobile": "9888877778"
		}).insert()

		self.assertTrue(emp_override.name.startswith("EXT-"))
		self.assertNotEqual(emp_override.name, "MANUAL-OVERRIDE-CODE")
		self.assertEqual(emp_override.employee_code, emp_override.name)

	def test_external_employee_personal_fields_refused_fr75(self):
		"""FR-75, Rule 9: External employee cannot hold DOB, Aadhaar, Permanent Address."""
		# DOB violation
		emp_dob = frappe.get_doc({
			"doctype": "Tracora Employee",
			"company": "Test External Agency",
			"employee_name": "Contractor DOB",
			"mobile": "9800000001",
			"date_of_birth": "1995-05-15"
		})
		with self.assertRaises(frappe.ValidationError):
			emp_dob.insert()

		# Aadhaar violation
		emp_aadhaar = frappe.get_doc({
			"doctype": "Tracora Employee",
			"company": "Test External Agency",
			"employee_name": "Contractor Aadhaar",
			"mobile": "9800000002",
			"aadhaar_number": "123456789012"
		})
		with self.assertRaises(frappe.ValidationError):
			emp_aadhaar.insert()

		# Permanent address violation
		emp_addr = frappe.get_doc({
			"doctype": "Tracora Employee",
			"company": "Test External Agency",
			"employee_name": "Contractor Address",
			"mobile": "9800000003",
			"permanent_address": "456 Village Rd"
		})
		with self.assertRaises(frappe.ValidationError):
			emp_addr.insert()

	def test_internal_vs_external_branch_department_rules_fr72(self):
		"""FR-72: Internal manual entry requires branch & department; External does not."""
		# Internal employee with missing branch/dept -> Refused
		emp_code = "EMP-TEST-001"
		if frappe.db.exists("Tracora Employee", emp_code):
			frappe.delete_doc("Tracora Employee", emp_code, force=1)

		emp_no_branch = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": emp_code,
			"company": "Test Internal Corp",
			"employee_name": "Internal Staff 1",
			"mobile": "9700000001",
			"source": "Tracora"
		})
		with self.assertRaises(frappe.ValidationError):
			emp_no_branch.insert()

		# Ensure branch & dept exist for TIC
		if not frappe.db.exists("Tracora Branch", "Chennai - TIC"):
			frappe.get_doc({
				"doctype": "Tracora Branch",
				"branch_name": "Chennai",
				"company": "Test Internal Corp"
			}).insert()

		if not frappe.db.exists("Tracora Department", "Operations - TIC"):
			frappe.get_doc({
				"doctype": "Tracora Department",
				"department_name": "Operations",
				"company": "Test Internal Corp"
			}).insert()

		# Internal employee with branch and dept -> Succeeds
		emp_valid = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": emp_code,
			"company": "Test Internal Corp",
			"branch": "Chennai - TIC",
			"department": "Operations - TIC",
			"employee_name": "Internal Staff 1",
			"mobile": "9700000001",
			"source": "Tracora",
			"aadhaar_number": "999988887777"
		}).insert()
		self.assertEqual(emp_valid.name, emp_code)

		# External employee without branch or dept -> Succeeds
		emp_ext = frappe.get_doc({
			"doctype": "Tracora Employee",
			"company": "Test External Agency",
			"employee_name": "External Staff Without Branch",
			"mobile": "9600000001"
		}).insert()
		self.assertTrue(emp_ext.name.startswith("EXT-"))

	def test_hrms_sourced_employee_and_aadhaar_ownership_fr06_rule9a(self):
		"""FR-06, Rule 9a: HRMS employee allows missing branch on sync; aadhaar is Tracora-owned and editable."""
		hrms_code = "HRMS-EMP-999"
		if frappe.db.exists("Tracora Employee", hrms_code):
			frappe.delete_doc("Tracora Employee", hrms_code, force=1)

		emp_hrms = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": hrms_code,
			"company": "Test Internal Corp",
			"employee_name": "HRMS Synced Staff",
			"mobile": "9500000001",
			"source": "HRMS",
			"hrms_employee": "EMP-999",
			"is_incomplete": 1,
			"aadhaar_number": "111122223333"
		}).insert()

		self.assertEqual(emp_hrms.name, hrms_code)
		self.assertEqual(emp_hrms.source, "HRMS")
		self.assertEqual(emp_hrms.aadhaar_number, "111122223333")

		# Rule 9a: Aadhaar is Tracora-owned and can be edited independently on Tracora without error
		emp_hrms.aadhaar_number = "444455556666"
		emp_hrms.save()
		self.assertEqual(emp_hrms.aadhaar_number, "444455556666")
