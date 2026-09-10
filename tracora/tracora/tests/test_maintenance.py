# Copyright (c) 2026, Kishore and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.api.assign import assign_asset, assign_to_employee
from tracora.api.maintenance import send_to_maintenance, close_maintenance, get_open_maintenance


class TestTracoraMaintenance(FrappeTestCase):
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

		# 4. Employees
		if not frappe.db.exists("Tracora Employee", "MNT-EMP-01"):
			frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_code": "MNT-EMP-01",
				"employee_name": "Alice Maint",
				"mobile": "9876540101",
				"company": "Test Internal Corp",
				"branch": "HQ - TIC",
				"department": "IT - TIC",
				"status": "Active",
				"source": "Tracora"
			}).insert()

		if not frappe.db.exists("Tracora Employee", "MNT-EMP-02"):
			frappe.get_doc({
				"doctype": "Tracora Employee",
				"employee_code": "MNT-EMP-02",
				"employee_name": "Bob Maint",
				"mobile": "9876540102",
				"company": "Test Internal Corp",
				"branch": "HQ - TIC",
				"department": "IT - TIC",
				"status": "Active",
				"source": "Tracora"
			}).insert()

	def _create_test_asset(self, serial, status="In Store", assigned_to=None):
		unique_serial = f"{serial}-{frappe.generate_hash(length=8)}"
		asset = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": f"Laptop {unique_serial}",
			"brand": "Dell",
			"model_number": "Latitude 7420",
			"serial_no": unique_serial,
			"owner_company": "Test Internal Corp",
			"holding_company": "Test Internal Corp",
			"branch": "HQ - TIC",
			"location": "Main Office",
			"is_shared": 0,
			"status": status,
			"assigned_to": assigned_to,
			"condition": "Good"
		})
		asset.insert()
		return asset

	def test_fr18_open_maintenance_log_and_movement(self):
		"""FR-18: Sending asset to maintenance opens log and records Maintenance Sent movement."""
		asset = self._create_test_asset("SN-MNT-OPEN")
		res = send_to_maintenance(
			asset=asset.name,
			vendor="Dell Authorised Service",
			reason="Battery replacement",
			due_date="2026-09-20"
		)

		asset.reload()
		self.assertEqual(asset.status, "Under Maintenance")

		# Check Maintenance Log
		log = frappe.get_doc("Tracora Maintenance Log", res["maintenance_log"])
		self.assertEqual(log.asset, asset.name)
		self.assertEqual(log.log_status, "Open")
		self.assertEqual(log.pre_maintenance_status, "In Store")
		self.assertEqual(log.vendor, "Dell Authorised Service")
		self.assertEqual(str(log.due_date), "2026-09-20")

		# Check Movement Log
		movements = frappe.get_all(
			"Tracora Asset Movement",
			filters={"asset": asset.name, "movement_type": "Maintenance Sent"},
			fields=["name", "from_status", "to_status", "movement_type"]
		)
		self.assertEqual(len(movements), 1)
		self.assertEqual(movements[0].from_status, "In Store")
		self.assertEqual(movements[0].to_status, "Under Maintenance")

		# Check get_open_maintenance API helper
		open_log = get_open_maintenance(asset.name)
		self.assertIsNotNone(open_log)
		self.assertEqual(open_log["name"], log.name)

	def test_cannot_assign_while_under_maintenance_fr58(self):
		"""FR-58: Refuse single and batch assignment when asset is Under Maintenance."""
		asset = self._create_test_asset("SN-MNT-NOASSIGN")
		send_to_maintenance(
			asset=asset.name,
			vendor="Dell Authorised Service",
			reason="Screen repair"
		)

		# 1. Single assignment via assign_asset
		with self.assertRaises(frappe.ValidationError):
			assign_asset(asset.name, "MNT-EMP-01")

		# 2. Batch assignment via assign_to_employee
		with self.assertRaises(frappe.ValidationError):
			assign_to_employee("MNT-EMP-01", [asset.name])

	def test_cannot_open_duplicate_maintenance_log_model_level(self):
		"""Model-level guard: Direct .insert() of a second Open log for same asset is refused."""
		asset = self._create_test_asset("SN-MNT-DUP")
		send_to_maintenance(
			asset=asset.name,
			vendor="Vendor A",
			reason="Keyboard repair"
		)

		# Direct insertion bypassing API
		second_log = frappe.get_doc({
			"doctype": "Tracora Maintenance Log",
			"asset": asset.name,
			"vendor": "Vendor B",
			"reason": "Motherboard issue",
			"log_status": "Open",
			"pre_maintenance_status": "Under Maintenance"
		})
		with self.assertRaises(frappe.ValidationError):
			second_log.insert()

	def test_close_without_condition_refused(self):
		"""FR-18: Closing maintenance without condition_on_return is refused."""
		asset = self._create_test_asset("SN-MNT-NOCOND")
		res = send_to_maintenance(
			asset=asset.name,
			vendor="Dell Care",
			reason="OS reinstallation"
		)

		with self.assertRaises(frappe.ValidationError):
			close_maintenance(res["maintenance_log"], condition_on_return=None)

	def test_close_normal_restores_status_and_logs_movement(self):
		"""FR-18: Normal close restores pre_maintenance_status and records Maintenance Returned movement."""
		# Start with an assigned asset
		asset = self._create_test_asset("SN-MNT-RESTORE", status="In Store")
		assign_asset(asset.name, "MNT-EMP-01")
		asset.reload()
		self.assertEqual(asset.status, "Assigned")

		# Send to maintenance
		res = send_to_maintenance(
			asset=asset.name,
			vendor="Dell Care",
			reason="Speaker replacement"
		)
		asset.reload()
		self.assertEqual(asset.status, "Under Maintenance")

		# Close maintenance
		close_res = close_maintenance(
			res["maintenance_log"],
			condition_on_return="Good",
			remarks="Speaker replaced successfully"
		)

		asset.reload()
		# Restores pre-maintenance status (Assigned)
		self.assertEqual(asset.status, "Assigned")
		self.assertEqual(asset.assigned_to, "MNT-EMP-01")
		self.assertEqual(asset.condition, "Good")

		# Movement log check
		movements = frappe.get_all(
			"Tracora Asset Movement",
			filters={"asset": asset.name, "movement_type": "Maintenance Returned"},
			fields=["name", "from_status", "to_status", "from_employee", "to_employee"]
		)
		self.assertEqual(len(movements), 1)
		self.assertEqual(movements[0].from_status, "Under Maintenance")
		self.assertEqual(movements[0].to_status, "Assigned")
		self.assertEqual(movements[0].from_employee, "MNT-EMP-01")
		self.assertEqual(movements[0].to_employee, "MNT-EMP-01")

	def test_beyond_repair_routes_to_retired_and_clears_holder(self):
		"""FR-18: Beyond repair closure sets status to Retired, clears holder, and attributes in movement."""
		asset = self._create_test_asset("SN-MNT-BEYOND", status="In Store")
		assign_asset(asset.name, "MNT-EMP-01")
		asset.reload()
		self.assertEqual(asset.status, "Assigned")

		res = send_to_maintenance(
			asset=asset.name,
			vendor="Dell Care",
			reason="Water damage"
		)

		close_res = close_maintenance(
			res["maintenance_log"],
			condition_on_return="Not Working",
			is_beyond_repair=True,
			remarks="Motherboard corroded and unrepairable"
		)

		asset.reload()
		self.assertEqual(asset.status, "Retired")
		self.assertEqual(asset.condition, "Not Working")
		self.assertIsNone(asset.assigned_to)
		self.assertIsNone(asset.assigned_on)

		# Verify Beyond Repair movement
		movements = frappe.get_all(
			"Tracora Asset Movement",
			filters={"asset": asset.name, "movement_type": "Beyond Repair"},
			fields=["name", "from_status", "to_status", "from_employee", "to_employee", "remarks"]
		)
		self.assertEqual(len(movements), 1)
		self.assertEqual(movements[0].from_status, "Under Maintenance")
		self.assertEqual(movements[0].to_status, "Retired")
		self.assertEqual(movements[0].from_employee, "MNT-EMP-01")
		self.assertIsNone(movements[0].to_employee)


	def test_close_normal_unassigned_restores_in_store(self):
		"""FR-18: Normal close of an unassigned asset restores status to In Store with no holder."""
		asset = self._create_test_asset("SN-MNT-UNASSIGNED", status="In Store")
		self.assertIsNone(asset.assigned_to)
		self.assertEqual(asset.status, "In Store")

		res = send_to_maintenance(
			asset=asset.name,
			vendor="Dell Care",
			reason="Preventative diagnostic"
		)

		asset.reload()
		self.assertEqual(asset.status, "Under Maintenance")

		close_res = close_maintenance(
			res["maintenance_log"],
			condition_on_return="Good",
			remarks="Diagnostics passed cleanly"
		)

		asset.reload()
		self.assertEqual(asset.status, "In Store")
		self.assertIsNone(asset.assigned_to)
		self.assertEqual(asset.condition, "Good")

		movements = frappe.get_all(
			"Tracora Asset Movement",
			filters={"asset": asset.name, "movement_type": "Maintenance Returned"},
			fields=["name", "from_status", "to_status", "from_employee", "to_employee", "recorded_by"]
		)
		self.assertEqual(len(movements), 1)
		self.assertEqual(movements[0].from_status, "Under Maintenance")
		self.assertEqual(movements[0].to_status, "In Store")
		self.assertIsNone(movements[0].from_employee)
		self.assertIsNone(movements[0].to_employee)
		self.assertEqual(movements[0].recorded_by, "Administrator")

	def test_employee_exit_holding_maintenance_asset_blocked_ec17(self):
		"""EC-1.7: Employee exit blocked when employee holds an asset that is currently Under Maintenance."""
		asset = self._create_test_asset("SN-MNT-EXITEMP", status="In Store")
		assign_asset(asset.name, "MNT-EMP-02")

		send_to_maintenance(
			asset=asset.name,
			vendor="Repair Shop",
			reason="Diagnostic test"
		)

		# Attempting to exit employee MNT-EMP-02 while holding asset in maintenance must be blocked
		emp = frappe.get_doc("Tracora Employee", "MNT-EMP-02")
		emp.status = "Exited"
		with self.assertRaises(frappe.ValidationError):
			emp.save()

	def test_double_close_refused(self):
		"""Idempotency / state guard: Closing already finalized log throws ValidationError."""
		asset = self._create_test_asset("SN-MNT-DBLCLOSE")
		res = send_to_maintenance(
			asset=asset.name,
			vendor="Vendor Quick",
			reason="Cleaning"
		)

		close_maintenance(res["maintenance_log"], condition_on_return="Good")

		# Attempting to close again
		with self.assertRaises(frappe.ValidationError):
			close_maintenance(res["maintenance_log"], condition_on_return="Good")

		# Direct modification to reopen
		log = frappe.get_doc("Tracora Maintenance Log", res["maintenance_log"])
		log.log_status = "Open"
		with self.assertRaises(frappe.ValidationError):
			log.save()
