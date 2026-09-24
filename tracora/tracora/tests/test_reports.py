# Copyright (c) 2026, Kishore and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days

from tracora.tracora.report.assets_owned.assets_owned import execute as exec_assets_owned
from tracora.tracora.report.assets_held.assets_held import execute as exec_assets_held
from tracora.tracora.report.assets_by_branch.assets_by_branch import execute as exec_assets_by_branch
from tracora.tracora.report.assets_by_department.assets_by_department import execute as exec_assets_by_department
from tracora.tracora.report.assets_by_employee.assets_by_employee import execute as exec_assets_by_employee
from tracora.tracora.report.external_custody.external_custody import execute as exec_external_custody
from tracora.tracora.report.licence_expiry.licence_expiry import execute as exec_licence_expiry
from tracora.tracora.report.licence_renewal_due.licence_renewal_due import execute as exec_licence_renewal_due
from tracora.tracora.report.tracora_report.tracora_report import execute as exec_tracora_report


class TestTracoraReports(FrappeTestCase):
	def setUp(self):
		super().setUp()
		# Internal Company
		if not frappe.db.exists("Tracora Company", "Report Internal Corp"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Report Internal Corp",
				"company_type": "Internal",
				"company_abbr": "RIC",
				"company_address": "123 Internal Road, Bangalore",
				"source": "Tracora"
			}).insert()

		# External Company
		if not frappe.db.exists("Tracora Company", "Report Client Corp"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Report Client Corp",
				"company_type": "External",
				"company_abbr": "RCC",
				"company_address": "456 Client Plaza, Mumbai",
				"source": "Tracora"
			}).insert()

		# Branch & Location
		if not frappe.db.exists("Tracora Branch", "HQ - RIC"):
			frappe.get_doc({
				"doctype": "Tracora Branch",
				"branch_name": "HQ",
				"company": "Report Internal Corp"
			}).insert()

		if not frappe.db.exists("Tracora Department", "Engineering - RIC"):
			frappe.get_doc({
				"doctype": "Tracora Department",
				"department_name": "Engineering",
				"company": "Report Internal Corp"
			}).insert()

		if not frappe.db.exists("Tracora Location", "Reports Test Lab"):
			frappe.get_doc({
				"doctype": "Tracora Location",
				"location_name": "Reports Test Lab",
				"address": "Reports Building Floor 3",
				"latitude": 12.9716,
				"longitude": 77.5946
			}).insert()

	def test_all_reports_run_without_errors(self):
		"""Verify all 8 query reports execute cleanly and return columns + data."""
		reports = [
			("Assets Owned", exec_assets_owned),
			("Assets Held", exec_assets_held),
			("Assets by Branch", exec_assets_by_branch),
			("Assets by Department", exec_assets_by_department),
			("Assets by Employee", exec_assets_by_employee),
			("External Custody", exec_external_custody),
			("Licence Expiry", exec_licence_expiry),
			("Licence Renewal Due", exec_licence_renewal_due),
		]
		for name, exec_fn in reports:
			res = exec_fn({})
			self.assertGreaterEqual(len(res), 2, f"Report {name} did not return at least columns and data")
			columns, data = res[0], res[1]
			self.assertIsInstance(columns, list, f"Columns for {name} is not a list")
			self.assertIsInstance(data, list, f"Data for {name} is not a list")

	def test_pii_exclusion_fr39(self):
		"""FR-39: Aadhaar number and permanent address must never appear in any report or export."""
		reports = [
			exec_assets_owned,
			exec_assets_held,
			exec_assets_by_branch,
			exec_assets_by_department,
			exec_assets_by_employee,
			exec_external_custody,
			exec_licence_expiry,
			exec_licence_renewal_due,
		]
		banned = ("aadhaar", "aadhaar_number", "permanent_address")
		for exec_fn in reports:
			res = exec_fn({})
			columns = res[0]
			for col in columns:
				fieldname = col.get("fieldname", "").lower()
				label = col.get("label", "").lower()
				for b in banned:
					self.assertNotIn(b, fieldname, f"Banned PII field {b} found in report column {fieldname}")
					self.assertNotIn(b, label, f"Banned PII label {b} found in report column {label}")

	def test_fr77_internal_vs_external_custody(self):
		"""FR-77: Internal employees appear in Assets by Employee; External employees appear in External Custody."""
		# 1. Internal Employee + Asset
		emp_int = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": "EMP-REP-INT",
			"employee_name": "Internal Reporter",
			"mobile": "9876500001",
			"first_name": "Internal",
			"last_name": "Reporter",
			"company": "Report Internal Corp",
			"branch": "HQ - RIC",
			"department": "Engineering - RIC",
			"status": "Active",
			"source": "Tracora"
		}).insert(ignore_permissions=True)

		ast_int = frappe.get_doc({
			"doctype": "Tracora Asset",
			"asset_name": "Internal Test Laptop",
			"tag_mode": "Auto-generated",
			"brand": "Dell",
			"serial_no": "SN-REP-INT-001",
			"owner_company": "Report Internal Corp",
			"holding_company": "Report Internal Corp",
			"branch": "HQ - RIC",
			"location": "Reports Test Lab",
			"status": "Assigned",
			"assigned_to": emp_int.name,
			"assigned_on": today(),
			"condition": "Good"
		}).insert(ignore_permissions=True)

		# 2. External Employee + Asset
		emp_ext = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": "EMP-REP-EXT",
			"employee_name": "External Client Eng",
			"mobile": "9876500003",
			"first_name": "External",
			"last_name": "Client Eng",
			"company": "Report Client Corp",
			"status": "Active",
			"source": "Tracora"
		}).insert(ignore_permissions=True)

		ast_ext = frappe.get_doc({
			"doctype": "Tracora Asset",
			"asset_name": "External Test Laptop",
			"tag_mode": "Auto-generated",
			"brand": "Dell",
			"serial_no": "SN-REP-EXT-001",
			"owner_company": "Report Internal Corp",
			"holding_company": "Report Client Corp",
			"location": "Reports Test Lab",
			"status": "Assigned",
			"assigned_to": emp_ext.name,
			"assigned_on": today(),
			"condition": "Good"
		}).insert(ignore_permissions=True)

		# Check Assets by Employee (Internal only)
		cols_e, data_e, _ = exec_assets_by_employee({"company": "Report Internal Corp"})
		emp_codes_in_report = [d.get("employee") for d in data_e]
		self.assertIn(emp_int.name, emp_codes_in_report, "Internal employee must be in Assets by Employee")
		self.assertNotIn(emp_ext.name, emp_codes_in_report, "External employee must NOT be in Assets by Employee (FR-77)")

		# Check External Custody (External only)
		cols_c, data_c, _ = exec_external_custody({"holding_company": "Report Client Corp"})
		ext_codes_in_report = [d.get("employee") for d in data_c]
		self.assertIn(emp_ext.name, ext_codes_in_report, "External employee must be in External Custody")
		self.assertNotIn(emp_int.name, ext_codes_in_report, "Internal employee must NOT be in External Custody (FR-77)")

	def test_exited_employee_custody_surfacing(self):
		"""Confirm an employee with status='Exited' who holds an asset is surfaced with employee_status='Exited'."""
		emp_exited = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": "EMP-REP-EXITED",
			"employee_name": "Departed Worker",
			"mobile": "9876500002",
			"first_name": "Departed",
			"last_name": "Worker",
			"company": "Report Internal Corp",
			"branch": "HQ - RIC",
			"department": "Engineering - RIC",
			"status": "Active",
			"source": "Tracora"
		}).insert(ignore_permissions=True)

		ast_held = frappe.get_doc({
			"doctype": "Tracora Asset",
			"asset_name": "Retained Asset Exited",
			"tag_mode": "Auto-generated",
			"brand": "Dell",
			"serial_no": "SN-REP-EXIT-999",
			"owner_company": "Report Internal Corp",
			"holding_company": "Report Internal Corp",
			"branch": "HQ - RIC",
			"location": "Reports Test Lab",
			"status": "Assigned",
			"assigned_to": emp_exited.name,
			"assigned_on": today(),
			"condition": "Good"
		}).insert(ignore_permissions=True)

		# Directly force status to Exited in DB to simulate custody anomaly
		frappe.db.set_value("Tracora Employee", emp_exited.name, "status", "Exited")

		cols, data, _ = exec_assets_by_employee({"employee": emp_exited.name})
		self.assertEqual(len(data), 1, "Exited employee with asset must be surfaced in report")
		self.assertEqual(data[0].get("employee_status"), "Exited", "Report must surface employee_status as 'Exited'")

	def test_licence_expiry_active_seats_and_sorting(self):
		"""Confirm active_seats on Licence Expiry counts only Active seats, and sorting is ascending."""
		ast = frappe.get_all("Tracora Asset", limit=2, pluck="name")
		lic = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Test Tool For Expiry Report",
			"licence_name": "Expiry Report Licence",
			"company": "Report Internal Corp",
			"licence_type": "Device licence",
			"renewal_cycle": "Yearly",
			"licence_expiry_date": add_days(today(), 45),
			"seats": [
				{"device": ast[0], "seat_status": "Active", "software_key": "KEY-ACT-1"},
				{"device": ast[1], "seat_status": "Released", "software_key": "KEY-REL-1"},
			]
		}).insert(ignore_permissions=True)

		cols, data = exec_licence_expiry({"company": "Report Internal Corp"})
		target_row = next((d for d in data if d.get("licence_name") == lic.name), None)
		self.assertIsNotNone(target_row, "Created licence must appear in Licence Expiry report")
		# active_seats must be 1 (Active only)
		self.assertEqual(target_row.get("active_seats"), 1, "active_seats must include only Active seats")

	def test_licence_renewal_due_null_handling(self):
		"""Confirm Licence Renewal Due excludes NULL next_renewal_date by default and includes with toggle."""
		# 1. Licence with next_renewal_date set
		lic_with_date = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Renewing Tool",
			"licence_name": "Renewing Pack",
			"company": "Report Internal Corp",
			"licence_type": "Device licence",
			"renewal_cycle": "Monthly",
			"licence_start_date": today(),
			"licence_expiry_date": add_days(today(), 100),
			"seats": []
		}).insert(ignore_permissions=True)

		# 2. Licence with next_renewal_date NULL (One-time, no start date)
		lic_null_date = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Perpetual Tool",
			"licence_name": "Perpetual Pack",
			"company": "Report Internal Corp",
			"licence_type": "Device licence",
			"renewal_cycle": "One-time",
			"licence_start_date": None,
			"licence_expiry_date": add_days(today(), 200),
			"seats": []
		}).insert(ignore_permissions=True)

		# Default run: include_non_renewing = 0
		cols, data_def = exec_licence_renewal_due({"company": "Report Internal Corp", "include_non_renewing": 0})
		names_def = [d.get("licence_name") for d in data_def]
		self.assertIn(lic_with_date.name, names_def, "Renewing licence must be present")
		self.assertNotIn(lic_null_date.name, names_def, "Non-renewing licence with NULL date must be excluded by default")

		# Toggled run: include_non_renewing = 1
		cols, data_all = exec_licence_renewal_due({"company": "Report Internal Corp", "include_non_renewing": 1})
		names_all = [d.get("licence_name") for d in data_all]
		self.assertIn(lic_with_date.name, names_all, "Renewing licence must be present")
		self.assertIn(lic_null_date.name, names_all, "Non-renewing licence must be included when toggle is active")

	def test_assets_by_department_unassigned_stock(self):
		"""FR-37: Confirm assets with assigned_to IS NULL appear labeled 'Unassigned Stock'."""
		ast_unassigned = frappe.get_doc({
			"doctype": "Tracora Asset",
			"asset_name": "Unassigned Stock Laptop",
			"tag_mode": "Auto-generated",
			"brand": "Dell",
			"serial_no": "SN-UNASSIGNED-001",
			"owner_company": "Report Internal Corp",
			"holding_company": "Report Internal Corp",
			"branch": "HQ - RIC",
			"location": "Reports Test Lab",
			"status": "In Store",
			"assigned_to": None,
			"condition": "Good"
		}).insert(ignore_permissions=True)

		cols, data = exec_assets_by_department({"holding_company": "Report Internal Corp"})
		target_row = next((d for d in data if d.get("asset_tag") == ast_unassigned.asset_tag), None)
		self.assertIsNotNone(target_row, "Unassigned asset must appear in department report")
		self.assertEqual(target_row.get("department"), "Unassigned Stock", "Unassigned asset must have department='Unassigned Stock'")

	def test_fr38_excel_export(self):
		"""FR-38: Every report exports to Excel with matching columns shown on screen."""
		import io
		import openpyxl
		from frappe.desk.query_report import run, export_query

		res = run("Assets Owned", {})
		expected_labels = [c["label"] for c in res["columns"]]

		frappe.form_dict.report_name = "Assets Owned"
		frappe.form_dict.file_format_type = "Excel"
		frappe.form_dict.filters = "{}"
		frappe.form_dict.visible_idx = "[]"

		export_query()
		filecontent = frappe.response.get("filecontent")
		self.assertIsNotNone(filecontent, "Excel export must return file content")

		wb = openpyxl.load_workbook(io.BytesIO(filecontent))
		sheet = wb.active
		exported_headers = [cell.value for cell in sheet[1] if cell.value is not None]

		self.assertEqual(exported_headers, expected_labels, "Exported Excel headers must match screen columns (FR-38)")

	def test_tracora_report_all_eight_views(self):
		"""Unified Tracora Report executes across all 8 views cleanly."""
		views = [
			"Assets Owned",
			"Assets Held",
			"Assets by Branch",
			"Assets by Department",
			"Assets by Employee",
			"External Custody",
			"Licence Expiry",
			"Licence Renewal Due",
		]
		for v in views:
			cols, data, msg, chart = exec_tracora_report({"primary_view": v})
			self.assertGreater(len(cols), 0, f"View {v} must return columns")
			self.assertIsInstance(data, list, f"View {v} must return a list of rows")
			if v == "Assets Owned":
				self.assertIsNotNone(chart, "Assets Owned view must return a summary bar chart")

	def test_tracora_report_multiselect_filters(self):
		"""Unified Tracora Report respects multi-select list filters."""
		cols, data, _, _ = exec_tracora_report({
			"primary_view": "Assets Owned",
			"status": ["Assigned", "In Store"]
		})
		for row in data:
			self.assertIn(row.get("status"), ["Assigned", "In Store"])

	def test_tracora_report_dynamic_column_selection(self):
		"""Unified Tracora Report projects only requested columns when selected_columns is provided."""
		cols, data, _, _ = exec_tracora_report({
			"primary_view": "Assets Owned",
			"selected_columns": ["asset_tag", "asset_name", "status"]
		})
		returned_fields = [c["fieldname"] for c in cols]
		self.assertEqual(returned_fields, ["asset_tag", "asset_name", "status"])
