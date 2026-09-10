# Copyright (c) 2026, Kishore and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.api.assign import (
	assign_asset,
	assign_to_employee,
	unassign_asset,
	transfer_ownership,
	recover_asset,
	get_movement_history
)


class TestTracoraMovements(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

		# 1. Company
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

		# 2. Branch & Department
		if not frappe.db.exists("Tracora Branch", "HQ - TIC"):
			frappe.get_doc({
				"doctype": "Tracora Branch",
				"branch_name": "HQ",
				"company": "Test Internal Corp",
				"source": "Tracora"
			}).insert()

		if not frappe.db.exists("Tracora Department", "IT - TIC"):
			frappe.get_doc({
				"doctype": "Tracora Department",
				"department_name": "IT",
				"company": "Test Internal Corp",
				"source": "Tracora"
			}).insert()

		# 3. Location
		if not frappe.db.exists("Tracora Location", "Main Office"):
			frappe.get_doc({
				"doctype": "Tracora Location",
				"location_name": "Main Office",
				"address": "100 IT Park, Chennai",
				"latitude": 13.0827,
				"longitude": 80.2707
			}).insert()

		if not frappe.db.exists("Tracora Location", "Warehouse"):
			frappe.get_doc({
				"doctype": "Tracora Location",
				"location_name": "Warehouse",
				"address": "200 Supply Rd, Chennai",
				"latitude": 13.0850,
				"longitude": 80.2750
			}).insert()

		# 4. Employees
		if not frappe.db.exists("Tracora Employee", "MOV-EMP-01"):
			frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_code": "MOV-EMP-01",
				"employee_name": "Alice M",
				"mobile": "9876540001",
				"company": "Test Internal Corp",
				"branch": "HQ - TIC",
				"department": "IT - TIC",
				"status": "Active",
				"source": "Tracora"
			}).insert()

		if not frappe.db.exists("Tracora Employee", "MOV-EMP-02"):
			frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_code": "MOV-EMP-02",
				"employee_name": "Bob M",
				"mobile": "9876540002",
				"company": "Test Internal Corp",
				"branch": "HQ - TIC",
				"department": "IT - TIC",
				"status": "Active",
				"source": "Tracora"
			}).insert()

		if not frappe.db.exists("Tracora Employee", "MOV-EMP-EXIT"):
			frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_code": "MOV-EMP-EXIT",
				"employee_name": "Charlie Exited",
				"mobile": "9876540003",
				"company": "Test Internal Corp",
				"branch": "HQ - TIC",
				"department": "IT - TIC",
				"status": "Exited",
				"source": "Tracora"
			}).insert()

		if not frappe.db.exists("Tracora Employee", "MOV-EMP-PEND"):
			frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_code": "MOV-EMP-PEND",
				"employee_name": "Diana Pending",
				"mobile": "9876540004",
				"company": "Test Internal Corp",
				"branch": "HQ - TIC",
				"department": "IT - TIC",
				"status": "Pending Clearance",
				"source": "Tracora"
			}).insert()

	def _create_test_asset(self, serial, name_prefix="Laptop", is_shared=0, status="In Store"):
		unique_serial = f"{serial}-{frappe.generate_hash(length=8)}"
		asset = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": f"{name_prefix} {unique_serial}",
			"brand": "Dell",
			"model_number": "Latitude 7420",
			"serial_no": unique_serial,
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Main Office",
			"is_shared": is_shared,
			"status": status,
			"condition": "Good"
		})
		asset.insert()
		return asset

	def test_fr50_assign_single_vs_batch_identical(self):
		"""FR-50: Same assignment made via assign_asset and assign_to_employee yields identical asset state and movement log fields."""
		a1 = self._create_test_asset("SN-FR50-A1")
		a2 = self._create_test_asset("SN-FR50-A2")
		ref = "REF-FR50"
		remarks = "Q3 Refresh"

		# Route A: assign_asset
		res1 = assign_asset(a1.name, "MOV-EMP-01", reference=ref, remarks=remarks)
		# Route B: assign_to_employee
		res2 = assign_to_employee("MOV-EMP-01", [a2.name], reference=ref, remarks=remarks)

		a1.reload()
		a2.reload()

		# Compare asset states
		self.assertEqual(a1.status, a2.status)
		self.assertEqual(a1.status, "Assigned")
		self.assertEqual(a1.assigned_to, a2.assigned_to)
		self.assertEqual(a1.assigned_to, "MOV-EMP-01")
		self.assertEqual(a1.assigned_on, a2.assigned_on)
		self.assertEqual(a1.holding_company, a2.holding_company)
		self.assertEqual(a1.branch, a2.branch)

		# Compare movement log entries
		m1 = frappe.get_doc("Tracora Asset Movement", res1["movement"])
		m2 = frappe.get_doc("Tracora Asset Movement", res2["items"][0]["movement"])

		self.assertEqual(m1.movement_type, m2.movement_type)
		self.assertEqual(m1.movement_type, "Assign")
		self.assertIsNone(m1.from_employee)
		self.assertEqual(m1.to_employee, "MOV-EMP-01")
		self.assertEqual(m1.from_company, m2.from_company)
		self.assertEqual(m1.to_company, m2.to_company)
		self.assertEqual(m1.from_location, m2.from_location)
		self.assertEqual(m1.to_location, m2.to_location)
		self.assertEqual(m1.from_status, m2.from_status)
		self.assertEqual(m1.to_status, m2.to_status)
		self.assertEqual(m1.remarks, m2.remarks)
		self.assertEqual(m1.remarks, remarks)
		self.assertEqual(m1.recorded_by, m2.recorded_by)

	def test_fr51_unassign_mandatory_remarks(self):
		"""FR-51: unassign_asset with empty remarks is refused with ValidationError; with remarks succeeds and logs movement."""
		a = self._create_test_asset("SN-FR51")
		assign_asset(a.name, "MOV-EMP-01", remarks="Initial")

		# Blank remarks refused
		with self.assertRaises(frappe.ValidationError) as ctx:
			unassign_asset(a.name, location="Warehouse", remarks="")
		self.assertIn("Remarks are mandatory", str(ctx.exception))

		# Whitespace remarks refused
		with self.assertRaises(frappe.ValidationError):
			unassign_asset(a.name, location="Warehouse", remarks="   ")

		# With remarks succeeds
		res = unassign_asset(a.name, location="Warehouse", remarks="Returned due to project end", condition="Fair", status="In Store")
		a.reload()
		self.assertIsNone(a.assigned_to)
		self.assertIsNone(a.assigned_on)
		self.assertEqual(a.location, "Warehouse")
		self.assertEqual(a.status, "In Store")
		self.assertEqual(a.condition, "Fair")

		m = frappe.get_doc("Tracora Asset Movement", res["movement"])
		self.assertEqual(m.movement_type, "Unassign")
		self.assertEqual(m.from_employee, "MOV-EMP-01")
		self.assertIsNone(m.to_employee)
		self.assertEqual(m.remarks, "Returned due to project end")

	def test_fr57_assign_already_assigned_refused(self):
		"""FR-57: Assigning an already-assigned asset is refused, naming the current holder."""
		a = self._create_test_asset("SN-FR57")
		assign_asset(a.name, "MOV-EMP-01", remarks="Given to Alice")

		with self.assertRaises(frappe.ValidationError) as ctx:
			assign_asset(a.name, "MOV-EMP-02", remarks="Try assign to Bob")
		err_msg = str(ctx.exception)
		self.assertIn("already assigned", err_msg)
		self.assertTrue("Alice M" in err_msg or "MOV-EMP-01" in err_msg)
		self.assertIn("FR-57", err_msg)

	def test_fr58_assign_invalid_status_refused(self):
		"""FR-58: Assigning an asset with status Under Maintenance, Lost, or Retired is refused."""
		for bad_status in ("Under Maintenance", "Lost", "Retired"):
			a = self._create_test_asset(f"SN-FR58-{bad_status[:4]}", status=bad_status)
			with self.assertRaises(frappe.ValidationError) as ctx:
				assign_asset(a.name, "MOV-EMP-01")
			self.assertIn(bad_status, str(ctx.exception))
			self.assertIn("FR-58", str(ctx.exception))

	def test_fr69_assign_exited_or_pending_clearance_refused(self):
		"""FR-69: Assigning to an employee with status Exited or Pending Clearance is refused."""
		a1 = self._create_test_asset("SN-FR69-1")
		with self.assertRaises(frappe.ValidationError) as ctx1:
			assign_asset(a1.name, "MOV-EMP-EXIT")
		self.assertIn("Exited", str(ctx1.exception))
		self.assertIn("FR-69", str(ctx1.exception))

		a2 = self._create_test_asset("SN-FR69-2")
		with self.assertRaises(frappe.ValidationError) as ctx2:
			assign_asset(a2.name, "MOV-EMP-PEND")
		self.assertIn("Pending Clearance", str(ctx2.exception))
		self.assertIn("FR-69", str(ctx2.exception))

	def test_fr69_pending_clearance_auto_cleared_on_last_unassign(self):
		"""FR-69: Pending Clearance clears to Exited automatically on last release."""
		emp_code = f"MOV-PND-{frappe.generate_hash(length=6)}"
		emp = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": emp_code,
			"employee_name": "Pending Clear Tester",
			"mobile": "9876540099",
			"company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"department": "IT - TIC",
			"status": "Active",
			"source": "Tracora"
		}).insert()

		a = self._create_test_asset("SN-FR69-CLEAR")
		assign_asset(a.name, emp.name)

		# HRMS sets status to Pending Clearance
		emp.status = "Pending Clearance"
		emp.save()

		# Unassign the asset
		unassign_asset(a.name, location="Main Office", remarks="Exit turnover clearance")

		# Verify employee is automatically transitioned to Exited
		emp.reload()
		self.assertEqual(emp.status, "Exited")

	def test_fr93_assign_shared_equipment_refused(self):
		"""FR-93: Assigning an asset with is_shared == 1 via assign_asset is refused upfront with the FR-93 message."""
		a = self._create_test_asset("SN-FR93-PRN", name_prefix="Printer", is_shared=1)

		with self.assertRaises(frappe.ValidationError) as ctx:
			assign_asset(a.name, "MOV-EMP-01")
		self.assertIn("marked as shared equipment and cannot be assigned to an individual (FR-93)", str(ctx.exception))

	def test_fr17_movement_history_append_only(self):
		"""FR-17 / Rule 2: Editing a saved movement's remarks as Administrator throws ValidationError; deleting throws ValidationError."""
		a = self._create_test_asset("SN-FR17")
		res = assign_asset(a.name, "MOV-EMP-01", remarks="Original remarks")

		movement = frappe.get_doc("Tracora Asset Movement", res["movement"])

		# Edit attempt as Administrator
		movement.remarks = "Tampered remarks"
		with self.assertRaises(frappe.ValidationError) as ctx_edit:
			movement.save()
		self.assertIn("History records cannot be edited", str(ctx_edit.exception))

		# Delete attempt as Administrator
		with self.assertRaises(frappe.ValidationError) as ctx_del:
			movement.delete()
		self.assertIn("History records cannot be deleted", str(ctx_del.exception))

	def test_fr82_transfer_ownership(self):
		"""FR-82: transfer_ownership changes owner and creates Ownership Transfer movement; direct form edit without flag remains refused."""
		a = self._create_test_asset("SN-FR82")
		self.assertEqual(a.owner_company, "Test Internal Corp")

		# Direct edit without flag is blocked
		a.owner_company = "Test External Agency"
		with self.assertRaises(frappe.ValidationError) as ctx:
			a.save()
		self.assertIn("Owner Company cannot be changed by editing", str(ctx.exception))

		# Legitimate transfer via transfer_ownership
		res = transfer_ownership(a.name, to_owner="Test External Agency", reason="Sold asset to external partner")
		a.reload()
		self.assertEqual(a.owner_company, "Test External Agency")

		m = frappe.get_doc("Tracora Asset Movement", res["movement"])
		self.assertEqual(m.movement_type, "Ownership Transfer")
		self.assertEqual(m.from_owner, "Test Internal Corp")
		self.assertEqual(m.to_owner, "Test External Agency")
		self.assertEqual(m.remarks, "Sold asset to external partner")

	def test_fr84_lost_asset_recovery_and_assignment(self):
		"""FR-84: Lost asset cannot be assigned; after recover_asset, status is Recovered and it can be assigned."""
		a = self._create_test_asset("SN-FR84", status="Lost")

		# Assigning Lost asset is refused
		with self.assertRaises(frappe.ValidationError) as ctx:
			assign_asset(a.name, "MOV-EMP-01")
		self.assertIn("Lost", str(ctx.exception))

		# Recover asset
		res = recover_asset(a.name, remarks="Found in server room closet", condition="Good")
		a.reload()
		self.assertEqual(a.status, "Recovered")
		self.assertEqual(a.condition, "Good")

		m = frappe.get_doc("Tracora Asset Movement", res["movement"])
		self.assertEqual(m.movement_type, "Recovered")
		self.assertEqual(m.remarks, "Found in server room closet")

		# Now assignment succeeds
		assign_res = assign_asset(a.name, "MOV-EMP-01", remarks="Reassigned after recovery")
		a.reload()
		self.assertEqual(a.status, "Assigned")
		self.assertEqual(a.assigned_to, "MOV-EMP-01")

	def test_fr87_delete_employee_with_history_refused(self):
		"""FR-87: Deleting an employee who has movement history is refused."""
		emp_code = f"MOV-DEL-{frappe.generate_hash(length=6)}"
		emp = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": emp_code,
			"employee_name": "Dave Delete Guard",
			"mobile": "9876540098",
			"company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"department": "IT - TIC",
			"status": "Active",
			"source": "Tracora"
		}).insert()

		a = self._create_test_asset("SN-FR87")
		assign_asset(a.name, emp.name, remarks="Assign for delete guard test")
		unassign_asset(a.name, location="Main Office", remarks="Unassign for delete guard test")

		with self.assertRaises(frappe.ValidationError) as ctx:
			emp.delete()
		self.assertIn("appear in asset movement history", str(ctx.exception))
		self.assertIn("FR-87", str(ctx.exception))

	def test_batch_assignment_atomicity(self):
		"""Confirm assign_to_employee rolls back entirely if any candidate asset fails validation."""
		a1 = self._create_test_asset("SN-BTCH-OK")
		a2 = self._create_test_asset("SN-BTCH-FL", status="Under Maintenance")
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError):
			assign_to_employee("MOV-EMP-01", [a1.name, a2.name])

		# Asset 1 must NOT be assigned; transaction rolled back cleanly
		a1.reload()
		self.assertEqual(a1.status, "In Store")
		self.assertIsNone(a1.assigned_to)

		# No movement was committed for a1
		m_count = frappe.db.count("Tracora Asset Movement", {"asset": a1.name})
		self.assertEqual(m_count, 0)
