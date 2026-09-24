# Copyright (c) 2026, Kishore and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from tracora.api.lookup import find_asset, get_session_info


class TestTracoraLookup(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

		# Base Internal Company
		if not frappe.db.exists("Tracora Company", "Lookup Internal Corp"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Lookup Internal Corp",
				"company_type": "Internal",
				"company_abbr": "LIC",
				"company_address": "123 Lookup Blvd, Chennai",
				"source": "Tracora",
			}).insert()

		# Base External Company
		if not frappe.db.exists("Tracora Company", "Lookup External Partner"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Lookup External Partner",
				"company_type": "External",
				"company_abbr": "LEP",
				"company_address": "456 Partner Rd, Chennai",
				"source": "Tracora",
			}).insert()

		# Internal Branch & Department
		if not frappe.db.exists("Tracora Branch", "HQ - LIC"):
			frappe.get_doc({
				"doctype": "Tracora Branch",
				"branch_name": "HQ",
				"company": "Lookup Internal Corp",
				"source": "Tracora",
			}).insert()

		if not frappe.db.exists("Tracora Department", "Engineering - LIC"):
			frappe.get_doc({
				"doctype": "Tracora Department",
				"department_name": "Engineering",
				"company": "Lookup Internal Corp",
				"source": "Tracora",
			}).insert()

		# Location (Requires latitude and longitude per FR-03)
		if not frappe.db.exists("Tracora Location", "Lookup Warehouse 1"):
			frappe.get_doc({
				"doctype": "Tracora Location",
				"location_name": "Lookup Warehouse 1",
				"address": "123 Storage Rd, Chennai",
				"latitude": 13.0827,
				"longitude": 80.2707,
				"source": "Tracora",
			}).insert()

		# Internal Employee
		if not frappe.db.exists("Tracora Employee", "EMP-LKP-INT-01"):
			frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_code": "EMP-LKP-INT-01",
				"employee_name": "Internal Test Worker",
				"company": "Lookup Internal Corp",
				"branch": "HQ - LIC",
				"department": "Engineering - LIC",
				"mobile": "+91 99887 76655",
				"email": "internal.worker@lookuptest.com",
				"aadhaar_number": "123456789012",
				"permanent_address": "10 Internal Resident St",
				"status": "Active",
				"source": "Tracora",
			}).insert()

		# External Employee (autonamed with EXT-.###### series)
		existing_ext = frappe.db.get_value(
			"Tracora Employee",
			{"company": "Lookup External Partner", "employee_name": "External Test Consultant"},
			"name",
		)
		if not existing_ext:
			ext_doc = frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_name": "External Test Consultant",
				"company": "Lookup External Partner",
				"designation": "Principal Consultant",
				"mobile": "+91 91234 56789",
				"email": "external.consultant@partner.com",
				"status": "Active",
				"source": "Tracora",
			}).insert()
			self.ext_emp_name = ext_doc.name
		else:
			self.ext_emp_name = existing_ext

	def test_exact_tag_lookup_resolves_asset(self):
		tag = "TAG-LKP-01"
		serial = "SN-LKP-TAG-01"
		if not frappe.db.exists("Tracora Asset", {"asset_tag": tag}):
			frappe.get_doc({
				"doctype": "Tracora Asset",
				"tag_mode": "Manual entry",
				"asset_tag": tag,
				"serial_no": serial,
				"asset_name": "Precision Test Workstation",
				"brand": "Dell",
				"model_number": "Precision 5570",
				"owner_company": "Lookup Internal Corp",
				"holding_company": "Lookup Internal Corp",
				"branch": "HQ - LIC",
				"location": "Lookup Warehouse 1",
				"status": "Assigned",
				"condition": "Good",
				"assigned_to": "EMP-LKP-INT-01",
			}).insert()

		res = find_asset(tag)
		self.assertEqual(res.get("match_type"), "single")
		self.assertEqual(res.get("query"), tag)
		self.assertIsNotNone(res.get("asset"))
		self.assertEqual(res["asset"]["asset_tag"], tag)
		self.assertEqual(res["asset"]["serial_no"], serial)
		self.assertEqual(res["asset"]["assigned_to"], "EMP-LKP-INT-01")

		# Holder present
		self.assertIsNotNone(res.get("holder"))
		self.assertEqual(res["holder"]["employee_code"], "EMP-LKP-INT-01")
		self.assertEqual(res["holder"]["employee_name"], "Internal Test Worker")

	def test_exact_serial_lookup_resolves_asset(self):
		tag = "TAG-LKP-SER-01"
		serial = "SN-LKP-SER-UNIQUE-99"
		if not frappe.db.exists("Tracora Asset", {"asset_tag": tag}):
			frappe.get_doc({
				"doctype": "Tracora Asset",
				"tag_mode": "Manual entry",
				"asset_tag": tag,
				"serial_no": serial,
				"asset_name": "Lenovo Test ThinkStation",
				"brand": "Lenovo",
				"model_number": "P360",
				"owner_company": "Lookup Internal Corp",
				"holding_company": "Lookup Internal Corp",
				"branch": "HQ - LIC",
				"location": "Lookup Warehouse 1",
				"status": "In Store",
				"condition": "New",
			}).insert()

		res = find_asset(serial)
		self.assertEqual(res.get("match_type"), "single")
		self.assertEqual(res.get("query"), serial)
		self.assertEqual(res["asset"]["asset_tag"], tag)
		self.assertEqual(res["asset"]["serial_no"], serial)
		self.assertIsNone(res.get("holder"))

	def test_exact_match_short_circuits_partial_search(self):
		"""
		If an exact asset_tag or serial_no match is found, return it immediately as
		a single match. Do NOT run the partial asset_name search in that case.
		"""
		exact_tag = "TAG-SHORT-01"
		# Asset A has exact tag 'TAG-SHORT-01'
		if not frappe.db.exists("Tracora Asset", {"asset_tag": exact_tag}):
			frappe.get_doc({
				"doctype": "Tracora Asset",
				"tag_mode": "Manual entry",
				"asset_tag": exact_tag,
				"serial_no": "SN-SHORT-EXACT-01",
				"asset_name": "Target Primary Workstation",
				"brand": "Dell",
				"model_number": "XPS 15",
				"owner_company": "Lookup Internal Corp",
				"holding_company": "Lookup Internal Corp",
				"branch": "HQ - LIC",
				"location": "Lookup Warehouse 1",
				"status": "In Store",
				"condition": "Good",
			}).insert()

		# Asset B and Asset C contain 'TAG-SHORT-01' in their asset_name
		for suffix in ["B", "C"]:
			other_tag = f"TAG-SHORT-OTHER-{suffix}"
			if not frappe.db.exists("Tracora Asset", {"asset_tag": other_tag}):
				frappe.get_doc({
					"doctype": "Tracora Asset",
					"tag_mode": "Manual entry",
					"asset_tag": other_tag,
					"serial_no": f"SN-SHORT-PARTIAL-{suffix}",
					"asset_name": f"Laptop matching {exact_tag} in name",
					"brand": "Dell",
					"model_number": "Latitude 5420",
					"owner_company": "Lookup Internal Corp",
					"holding_company": "Lookup Internal Corp",
					"branch": "HQ - LIC",
					"location": "Lookup Warehouse 1",
					"status": "In Store",
					"condition": "Good",
				}).insert()

		# Querying 'TAG-SHORT-01' must resolve directly to Asset A as 'single',
		# and must NOT return a multiple-match list with Assets B and C
		res = find_asset(exact_tag)
		self.assertEqual(res.get("match_type"), "single")
		self.assertEqual(res["asset"]["asset_tag"], exact_tag)
		self.assertNotIn("results", res)

	def test_multi_name_match_returns_list_never_guesses(self):
		"""
		Partial asset_name search matching multiple assets must return up to 20 rows
		as match_type: 'multiple', never guessing between them (FR-91).
		"""
		prefix = "SharedFleetBook"
		for i in range(1, 4):
			tag = f"TAG-MULTI-{i}"
			if not frappe.db.exists("Tracora Asset", {"asset_tag": tag}):
				frappe.get_doc({
					"doctype": "Tracora Asset",
					"tag_mode": "Manual entry",
					"asset_tag": tag,
					"serial_no": f"SN-MULTI-{i}",
					"asset_name": f"{prefix} Model Gen {i}",
					"brand": "HP",
					"model_number": f"EliteBook 840 G{i}",
					"owner_company": "Lookup Internal Corp",
					"holding_company": "Lookup Internal Corp",
					"branch": "HQ - LIC",
					"location": "Lookup Warehouse 1",
					"status": "In Store",
					"condition": "Good",
				}).insert()

		res = find_asset(prefix)
		self.assertEqual(res.get("match_type"), "multiple")
		self.assertEqual(res.get("query"), prefix)
		self.assertGreaterEqual(res.get("count"), 3)
		self.assertIsInstance(res.get("results"), list)

		returned_tags = [r["asset_tag"] for r in res["results"]]
		for i in range(1, 4):
			self.assertIn(f"TAG-MULTI-{i}", returned_tags)

	def test_not_found_creates_nothing(self):
		"""
		A search with no match returns match_type: 'none', names what was searched,
		and creates zero records (FR-34).
		"""
		unknown_query = "TAG-TOTALLY-NONEXISTENT-999"
		count_before = frappe.db.count("Tracora Asset")

		res = find_asset(unknown_query)
		self.assertEqual(res.get("match_type"), "none")
		self.assertEqual(res.get("query"), unknown_query)
		self.assertIn(unknown_query, res.get("message"))

		count_after = frappe.db.count("Tracora Asset")
		self.assertEqual(count_before, count_after)

	def test_internal_holder_excludes_contact_and_restricted_fields(self):
		"""
		Internal employee holder payload must strictly exclude mobile, email,
		aadhaar_number, and permanent_address.
		"""
		tag = "TAG-SEC-INT-01"
		if not frappe.db.exists("Tracora Asset", {"asset_tag": tag}):
			frappe.get_doc({
				"doctype": "Tracora Asset",
				"tag_mode": "Manual entry",
				"asset_tag": tag,
				"serial_no": "SN-SEC-INT-01",
				"asset_name": "Security Test Laptop Internal",
				"brand": "Apple",
				"model_number": "MacBook Air",
				"owner_company": "Lookup Internal Corp",
				"holding_company": "Lookup Internal Corp",
				"branch": "HQ - LIC",
				"location": "Lookup Warehouse 1",
				"status": "Assigned",
				"condition": "Good",
				"assigned_to": "EMP-LKP-INT-01",
			}).insert()

		res = find_asset(tag)
		holder = res.get("holder")
		self.assertIsNotNone(holder)

		# Required internal fields
		self.assertEqual(holder.get("employee_code"), "EMP-LKP-INT-01")
		self.assertEqual(holder.get("company_type"), "Internal")
		self.assertEqual(holder.get("branch"), "HQ - LIC")
		self.assertEqual(holder.get("department"), "Engineering - LIC")

		# Strictly forbidden fields
		self.assertNotIn("mobile", holder)
		self.assertNotIn("email", holder)
		self.assertNotIn("aadhaar_number", holder)
		self.assertNotIn("permanent_address", holder)

	def test_external_holder_shape(self):
		"""
		External employee holder provides designation and omits branch, department,
		mobile, and email.
		"""
		tag = "TAG-SEC-EXT-01"
		if not frappe.db.exists("Tracora Asset", {"asset_tag": tag}):
			frappe.get_doc({
				"doctype": "Tracora Asset",
				"tag_mode": "Manual entry",
				"asset_tag": tag,
				"serial_no": "SN-SEC-EXT-01",
				"asset_name": "Security Test Laptop External",
				"brand": "Apple",
				"model_number": "MacBook Pro",
				"owner_company": "Lookup Internal Corp",
				"holding_company": "Lookup External Partner",
				"branch": "HQ - LIC",
				"location": "Lookup Warehouse 1",
				"status": "Assigned",
				"condition": "Good",
				"assigned_to": self.ext_emp_name,
			}).insert()

		res = find_asset(tag)
		holder = res.get("holder")
		self.assertIsNotNone(holder)

		# Required external fields
		self.assertEqual(holder.get("employee_code"), self.ext_emp_name)
		self.assertEqual(holder.get("company_type"), "External")
		self.assertEqual(holder.get("designation"), "Principal Consultant")

		# Omitted for external
		self.assertNotIn("branch", holder)
		self.assertNotIn("department", holder)

		# Strictly forbidden contact/restricted fields
		self.assertNotIn("mobile", holder)
		self.assertNotIn("email", holder)
		self.assertNotIn("aadhaar_number", holder)
		self.assertNotIn("permanent_address", holder)

	def test_guest_lookup_refused(self):
		"""
		Guest session must be refused with frappe.PermissionError (FR-35).
		Asserts on exception type, not message string.
		"""
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				find_asset("TAG-LKP-01")
		finally:
			frappe.set_user("Administrator")

	def test_get_session_info_authenticated(self):
		"""
		get_session_info returns current user and a non-empty CSRF token.
		"""
		frappe.set_user("Administrator")
		info = get_session_info()
		self.assertIsInstance(info, dict)
		self.assertEqual(info.get("user"), "Administrator")
		self.assertTrue(bool(info.get("csrf_token")))

	def test_get_session_info_guest(self):
		"""
		get_session_info is callable by Guest under allow_guest=True.
		Asserts the response body contains exactly {"user": None, "csrf_token": "..."}
		with no additional fields, no server error details, and no session metadata.
		"""
		frappe.set_user("Guest")
		try:
			info = get_session_info()
			self.assertIsInstance(info, dict)
			self.assertEqual(set(info.keys()), {"user", "csrf_token"})
			self.assertIsNone(info.get("user"))
			self.assertIsInstance(info.get("csrf_token"), str)
			self.assertTrue(bool(info.get("csrf_token")))
		finally:
			frappe.set_user("Administrator")
