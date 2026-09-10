# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import json
from unittest.mock import patch
import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.integrations import hrms


class TestHRMSIntegration(FrappeTestCase):
	def setUp(self):
		# Ensure test roles
		for role in ["Tracora Super Admin", "Tracora Admin"]:
			if not frappe.db.exists("Role", role):
				frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)

		# Ensure test company in HRMS
		if not frappe.db.exists("Company", "HRMS Test Corp"):
			frappe.get_doc({
				"doctype": "Company",
				"company_name": "HRMS Test Corp",
				"abbr": "HTC",
				"default_currency": "INR",
				"country": "India"
			}).insert(ignore_permissions=True)

		# Ensure Tracora Company
		if not frappe.db.exists("Tracora Company", "HRMS Test Corp"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "HRMS Test Corp",
				"company_type": "Internal",
				"company_abbr": "HTC",
				"company_address": "Chennai",
				"source": "HRMS",
				"hrms_company": "HRMS Test Corp"
			}).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_hrms_employee_creation_and_sync(self):
		"""HRMS employee creation creates matching Tracora employee with source = HRMS."""
		emp_code = "HRMS-AUTO-001"
		if frappe.db.exists("Tracora Employee", emp_code):
			frappe.delete_doc("Tracora Employee", emp_code, force=1)

		hrms_doc = frappe._dict({
			"doctype": "Employee",
			"name": emp_code,
			"employee_name": "Ravi Kumar",
			"designation": "Engineer",
			"company": "HRMS Test Corp",
			"branch": "Chennai",
			"department": "Engineering",
			"cell_number": "9840012345",
			"company_email": "ravi.k@hrmstest.com",
			"date_of_birth": "1992-04-12",
			"permanent_address": "12 Gandhi St, Chennai",
			"status": "Active"
		})

		hrms.on_employee_change(hrms_doc)

		self.assertTrue(frappe.db.exists("Tracora Employee", emp_code))
		tracora_emp = frappe.get_doc("Tracora Employee", emp_code)
		self.assertEqual(tracora_emp.source, "HRMS")
		self.assertEqual(tracora_emp.hrms_employee, emp_code)
		self.assertEqual(tracora_emp.employee_name, "Ravi Kumar")
		self.assertEqual(tracora_emp.mobile, "9840012345")
		self.assertEqual(tracora_emp.permanent_address, "12 Gandhi St, Chennai")
		self.assertEqual(tracora_emp.status, "Active")

	def test_hrms_employee_update_mobile_and_address(self):
		"""HRMS employee update propagates fields to Tracora."""
		emp_code = "HRMS-AUTO-002"
		if frappe.db.exists("Tracora Employee", emp_code):
			frappe.delete_doc("Tracora Employee", emp_code, force=1)

		hrms_doc = frappe._dict({
			"doctype": "Employee",
			"name": emp_code,
			"employee_name": "Priya Sharma",
			"designation": "Analyst",
			"company": "HRMS Test Corp",
			"cell_number": "9840000001",
			"company_email": "priya@hrmstest.com",
			"status": "Active"
		})
		hrms.on_employee_change(hrms_doc)

		# Update mobile and permanent address in HRMS
		hrms_doc.cell_number = "9840099999"
		hrms_doc.permanent_address = "99 Anna Salai, Chennai"
		hrms.on_employee_change(hrms_doc)

		tracora_emp = frappe.get_doc("Tracora Employee", emp_code)
		self.assertEqual(tracora_emp.mobile, "9840099999")
		self.assertEqual(tracora_emp.permanent_address, "99 Anna Salai, Chennai")

	def test_aadhaar_independence_rule9a(self):
		"""Rule 9a: Aadhaar is Tracora-owned and never modified by HRMS sync."""
		emp_code = "HRMS-AUTO-003"
		if frappe.db.exists("Tracora Employee", emp_code):
			frappe.delete_doc("Tracora Employee", emp_code, force=1)

		hrms_doc = frappe._dict({
			"doctype": "Employee",
			"name": emp_code,
			"employee_name": "Karthik Raja",
			"company": "HRMS Test Corp",
			"cell_number": "9840000003",
			"status": "Active",
			"custom_aadhaar_number": "999999999999"  # Present in HRMS
		})
		hrms.on_employee_change(hrms_doc)

		tracora_emp = frappe.get_doc("Tracora Employee", emp_code)
		self.assertFalse(tracora_emp.aadhaar_number)

		# Set Aadhaar independently in Tracora
		tracora_emp.aadhaar_number = "123456789012"
		tracora_emp.save()

		# Trigger another sync from HRMS
		hrms_doc.cell_number = "9840011111"
		hrms.on_employee_change(hrms_doc)

		# Re-verify Tracora Aadhaar remains untouched
		tracora_emp.reload()
		self.assertEqual(tracora_emp.aadhaar_number, "123456789012")
		self.assertEqual(tracora_emp.mobile, "9840011111")

	def test_hrms_employee_rename(self):
		"""HRMS employee rename renames Tracora document without creating duplicates (FR-56)."""
		old_code = "HRMS-OLD-CODE"
		new_code = "HRMS-NEW-CODE"
		for code in [old_code, new_code]:
			if frappe.db.exists("Tracora Employee", code):
				frappe.delete_doc("Tracora Employee", code, force=1)

		hrms_doc = frappe._dict({
			"doctype": "Employee",
			"name": old_code,
			"employee_name": "Rename Test",
			"company": "HRMS Test Corp",
			"cell_number": "9840000004",
			"status": "Active"
		})
		hrms.on_employee_change(hrms_doc)

		count_before = frappe.db.count("Tracora Employee")

		# Simulate rename
		hrms.on_employee_rename(doc=hrms_doc, old=old_code, new=new_code)

		count_after = frappe.db.count("Tracora Employee")
		self.assertEqual(count_before, count_after)
		self.assertFalse(frappe.db.exists("Tracora Employee", old_code))
		self.assertTrue(frappe.db.exists("Tracora Employee", new_code))
		new_doc = frappe.get_doc("Tracora Employee", new_code)
		self.assertEqual(new_doc.employee_code, new_code)
		self.assertEqual(new_doc.hrms_employee, new_code)

	def test_hrms_employee_delete(self):
		"""HRMS employee deletion detaches HRMS link and flips source to Tracora."""
		emp_code = "HRMS-DEL-001"
		if frappe.db.exists("Tracora Employee", emp_code):
			frappe.delete_doc("Tracora Employee", emp_code, force=1)

		hrms_doc = frappe._dict({
			"doctype": "Employee",
			"name": emp_code,
			"employee_name": "Delete Test",
			"company": "HRMS Test Corp",
			"cell_number": "9840000005",
			"status": "Active"
		})
		hrms.on_employee_change(hrms_doc)

		# Delete from HRMS
		hrms.on_hrms_delete(hrms_doc)

		self.assertTrue(frappe.db.exists("Tracora Employee", emp_code))
		tracora_emp = frappe.get_doc("Tracora Employee", emp_code)
		self.assertEqual(tracora_emp.source, "Tracora")
		self.assertIsNone(tracora_emp.hrms_employee)

	def test_sync_conflict_on_value_mismatch(self):
		"""Manual Tracora employee with matching code and different values creates Tracora Sync Conflict."""
		emp_code = "MANUAL-EMP-001"
		if frappe.db.exists("Tracora Employee", emp_code):
			frappe.delete_doc("Tracora Employee", emp_code, force=1)

		# Ensure Tracora Branch/Dept for TIC
		if not frappe.db.exists("Tracora Company", "Test Internal Corp"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Test Internal Corp",
				"company_type": "Internal",
				"company_abbr": "TIC",
				"company_address": "Chennai"
			}).insert(ignore_permissions=True)

		if not frappe.db.exists("Tracora Branch", "Chennai - TIC"):
			frappe.get_doc({
				"doctype": "Tracora Branch",
				"branch_name": "Chennai",
				"company": "Test Internal Corp"
			}).insert(ignore_permissions=True)

		if not frappe.db.exists("Tracora Department", "Operations - TIC"):
			frappe.get_doc({
				"doctype": "Tracora Department",
				"department_name": "Operations",
				"company": "Test Internal Corp"
			}).insert(ignore_permissions=True)

		# Create manual Tracora record
		tracora_emp = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": emp_code,
			"employee_name": "Manual Name",
			"company": "Test Internal Corp",
			"branch": "Chennai - TIC",
			"department": "Operations - TIC",
			"mobile": "9999999999",
			"source": "Tracora"
		}).insert(ignore_permissions=True)

		# Clear old conflicts if any
		frappe.db.delete("Tracora Sync Conflict", {"reference_key": emp_code})

		# Trigger HRMS sync with differing mobile & employee_name
		hrms_doc = frappe._dict({
			"doctype": "Employee",
			"name": emp_code,
			"employee_name": "HRMS Different Name",
			"company": "Test Internal Corp",
			"cell_number": "8888888888",
			"status": "Active"
		})
		hrms.on_employee_change(hrms_doc)

		# Verify Tracora record unchanged
		tracora_emp.reload()
		self.assertEqual(tracora_emp.employee_name, "Manual Name")
		self.assertEqual(tracora_emp.mobile, "9999999999")
		self.assertEqual(tracora_emp.source, "Tracora")

		# Verify Conflict created
		conflict_name = frappe.db.get_value("Tracora Sync Conflict", {"reference_key": emp_code, "conflict_status": "Open"}, "name")
		self.assertIsNotNone(conflict_name)
		conflict = frappe.get_doc("Tracora Sync Conflict", conflict_name)
		self.assertEqual(conflict.conflict_type, "Value mismatch")
		self.assertIn("employee_name", conflict.differing_fields)
		self.assertIn("mobile", conflict.differing_fields)

	def test_subscriber_exception_isolation_all_subscribers(self):
		"""Rule 3 & Clarification 1/2: ALL 7 subscriber entry points swallow exceptions and log Subscriber failure."""
		# Ensure test record exists so rename/delete handlers reach execution
		if not frappe.db.exists("Tracora Employee", "FAIL-EMP-ISO"):
			frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_code": "FAIL-EMP-ISO",
				"company": "HRMS Test Corp",
				"employee_name": "Fail Iso",
				"mobile": "9999911111",
				"source": "HRMS",
				"hrms_employee": "FAIL-EMP-ISO"
			}).insert(ignore_permissions=True, ignore_links=True)

		subscribers = [
			("on_employee_change", hrms.on_employee_change, frappe._dict({"doctype": "Employee", "name": "FAIL-EMP-1"}), "apply_hrms_employee", {}),
			("on_employee_rename", hrms.on_employee_rename, frappe._dict({"doctype": "Employee", "name": "FAIL-EMP-ISO"}), "frappe.rename_doc", {"old": "FAIL-EMP-ISO", "new": "FAIL-EMP-NEW"}),
			("on_hrms_delete", hrms.on_hrms_delete, frappe._dict({"doctype": "Employee", "name": "FAIL-EMP-ISO"}), "frappe.db.set_value", {}),
			("on_company_change", hrms.on_company_change, frappe._dict({"doctype": "Company", "name": "FAIL-COMP-1"}), "_get_or_create_company", {}),
			("on_branch_change", hrms.on_branch_change, frappe._dict({"doctype": "Branch", "name": "FAIL-BRANCH-1"}), "_get_or_create_branch", {}),
			("on_branch_rename", hrms.on_branch_rename, frappe._dict({"doctype": "Branch", "name": "FAIL-BRANCH-2"}), "frappe.rename_doc", {"old": "FAIL-BRANCH-2", "new": "FAIL-BRANCH-NEW"}),
			("on_department_change", hrms.on_department_change, frappe._dict({"doctype": "Department", "name": "FAIL-DEPT-1"}), "_get_or_create_department", {}),
		]

		for name, fn, test_doc, target_patch, kwargs in subscribers:
			frappe.db.delete("Tracora Sync Conflict", {"reference_key": test_doc.name, "conflict_type": "Subscriber failure"})
			
			# If on_branch_rename, ensure dummy branch exists to trigger rename_doc
			if name == "on_branch_rename":
				if not frappe.db.exists("Tracora Branch", "FAIL-BRANCH-2 - HTC"):
					frappe.get_doc({
						"doctype": "Tracora Branch",
						"branch_name": "FAIL-BRANCH-2",
						"company": "HRMS Test Corp",
						"source": "HRMS",
						"hrms_branch": "FAIL-BRANCH-2"
					}).insert(ignore_permissions=True, ignore_links=True)

			patch_target = f"tracora.integrations.hrms.{target_patch}" if not target_patch.startswith("frappe.") else target_patch
			
			with patch(patch_target, side_effect=RuntimeError(f"Forced error in {name}")):
				try:
					# Must NOT raise any exception
					res = fn(test_doc, **kwargs)
					self.assertIsNone(res)
				except Exception as e:
					self.fail(f"Subscriber {name} leaked exception: {e}")

			# Verify Subscriber failure conflict was logged
			conflict_exists = frappe.db.exists("Tracora Sync Conflict", {
				"reference_key": test_doc.name,
				"conflict_type": "Subscriber failure"
			})
			self.assertTrue(conflict_exists, f"Subscriber failure conflict not found for {name}")

	def test_bulk_import_dry_run_vs_real(self):
		"""Clarification 3: bulk_import dry_run=True creates 0 rows, dry_run=False seeds records."""
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", "superadmin@test.local"):
			u = frappe.get_doc({
				"doctype": "User",
				"email": "superadmin@test.local",
				"first_name": "SuperAdmin",
				"roles": [{"role": "Tracora Super Admin"}]
			}).insert(ignore_permissions=True)
		else:
			u = frappe.get_doc("User", "superadmin@test.local")
			if not any(r.role == "Tracora Super Admin" for r in u.roles):
				u.append("roles", {"role": "Tracora Super Admin"})
				u.save(ignore_permissions=True)

		frappe.set_user("superadmin@test.local")

		# Ensure test HRMS employee exists in DB with required fields
		emp_hrms = frappe.get_doc({
			"doctype": "Employee",
			"employee_number": "EMP-BULK-TEST-99",
			"first_name": "Bulk Import Staff",
			"employee_name": "Bulk Import Staff",
			"gender": "Male",
			"date_of_joining": "2024-01-01",
			"custom_roles_responsibilities": "General",
			"ctc": 500000,
			"company": "HRMS Test Corp",
			"cell_number": "9111122222",
			"status": "Active"
		})
		emp_hrms.insert(ignore_permissions=True, ignore_mandatory=True)
		emp_name = emp_hrms.name

		if frappe.db.exists("Tracora Employee", emp_name):
			frappe.delete_doc("Tracora Employee", emp_name, force=1)

		count_before_dry = frappe.db.count("Tracora Employee")
		res_dry = hrms.bulk_import(dry_run=True)
		count_after_dry = frappe.db.count("Tracora Employee")

		# Row count MUST be identical
		self.assertEqual(count_before_dry, count_after_dry)
		self.assertFalse(frappe.db.exists("Tracora Employee", emp_name))
		self.assertTrue(res_dry.get("dry_run"))

		# Now run for real
		res_real = hrms.bulk_import(dry_run=False)
		self.assertFalse(res_real.get("dry_run"))
		self.assertTrue(frappe.db.exists("Tracora Employee", emp_name))

	def test_sync_conflict_resolve(self):
		"""Resolving a sync conflict marks it as Resolved."""
		conflict = frappe.get_doc({
			"doctype": "Tracora Sync Conflict",
			"reference_doctype": "Tracora Employee",
			"reference_key": "CONFLICT-RESOLVE-TEST",
			"conflict_type": "Value mismatch",
			"hrms_reference": "CONFLICT-RESOLVE-TEST",
			"differing_fields": "mobile",
			"hrms_values": json.dumps({"mobile": "123"}),
			"tracora_values": json.dumps({"mobile": "456"}),
			"conflict_status": "Open"
		}).insert(ignore_permissions=True)

		conflict.resolve()
		conflict.reload()
		self.assertEqual(conflict.conflict_status, "Resolved")
