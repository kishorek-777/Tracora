# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import json
from functools import wraps
import frappe
from frappe import _


def safe_subscriber(event_name: str, doctype: str):
	"""Decorator guaranteeing Rule 3 & HLD §6: Subscribers never throw or block HRMS operations."""
	def decorator(fn):
		@wraps(fn)
		def wrapper(doc, method=None, *args, **kwargs):
			try:
				if not frappe.db.exists("DocType", doctype):
					return None
				return fn(doc, method, *args, **kwargs)
			except Exception as e:
				try:
					frappe.log_error(
						title=f"Tracora HRMS subscriber failure: {doctype}.{event_name}",
						message=frappe.get_traceback()
					)
				except Exception:
					pass

				try:
					doc_name = getattr(doc, "name", str(doc)) if doc else "Unknown"
					# Record Subscriber failure conflict
					if frappe.db.exists("DocType", "Tracora Sync Conflict"):
						frappe.get_doc({
							"doctype": "Tracora Sync Conflict",
							"reference_doctype": f"Tracora {doctype}" if not doctype.startswith("Tracora") else doctype,
							"reference_key": str(doc_name),
							"conflict_type": "Subscriber failure",
							"hrms_reference": str(doc_name),
							"differing_fields": "Subscriber exception",
							"hrms_values": json.dumps({"error": str(e), "traceback": frappe.get_traceback()}),
							"tracora_values": json.dumps({"status": "Failed to process subscriber"}),
							"conflict_status": "Open",
						}).insert(ignore_permissions=True, ignore_links=True)
				except Exception:
					pass
				return None
		return wrapper
	return decorator


def _get_company_abbr(hrms_company_name: str) -> str:
	"""Computes or looks up the company abbreviation without requiring the Tracora Company to already exist."""
	if not hrms_company_name:
		return "COMP"

	abbr = frappe.db.get_value("Tracora Company", {"hrms_company": hrms_company_name}, "company_abbr")
	if not abbr and frappe.db.exists("Tracora Company", hrms_company_name):
		abbr = frappe.db.get_value("Tracora Company", hrms_company_name, "company_abbr")
	if abbr:
		return abbr

	if frappe.db.exists("Company", hrms_company_name):
		abbr = frappe.db.get_value("Company", hrms_company_name, "abbr")

	if not abbr:
		abbr = "".join([w[0].upper() for w in hrms_company_name.split() if w])[:5] or "COMP"

	# Ensure uniqueness against existing Tracora Companies
	base_abbr = abbr
	counter = 1
	while frappe.db.exists("Tracora Company", {"company_abbr": abbr}):
		abbr = f"{base_abbr}{counter}"
		counter += 1

	return abbr


def _get_or_create_company(hrms_company_name: str, dry_run: bool = False):
	"""Finds or creates a Tracora Company corresponding to HRMS Company."""
	if not hrms_company_name:
		return None

	# Look up by name or hrms_company
	existing = frappe.db.get_value("Tracora Company", {"hrms_company": hrms_company_name}, "name")
	if not existing and frappe.db.exists("Tracora Company", hrms_company_name):
		existing = hrms_company_name

	if existing:
		return existing

	if dry_run:
		return hrms_company_name

	# Fetch HRMS Company details if available
	address = "Company Address"
	if frappe.db.exists("Company", hrms_company_name):
		hrms_comp = frappe.get_doc("Company", hrms_company_name)
		address = getattr(hrms_comp, "company_address", None) or getattr(hrms_comp, "address", "Company Address")

	abbr = _get_company_abbr(hrms_company_name)

	comp_doc = frappe.get_doc({
		"doctype": "Tracora Company",
		"company_name": hrms_company_name,
		"company_type": "Internal",
		"company_abbr": abbr,
		"company_address": address or "Auto-synced from HRMS",
		"source": "HRMS",
		"hrms_company": hrms_company_name
	})
	comp_doc.insert(ignore_permissions=True)
	return comp_doc.name


def _get_or_create_branch(hrms_branch_name: str, company_name: str, dry_run: bool = False):
	"""Finds or creates a Tracora Branch corresponding to HRMS Branch under company."""
	if not hrms_branch_name or not company_name:
		return None

	tracora_comp = _get_or_create_company(company_name, dry_run=dry_run)
	comp_abbr = _get_company_abbr(company_name)
	expected_name = f"{hrms_branch_name} - {comp_abbr}"

	existing = frappe.db.get_value("Tracora Branch", {"hrms_branch": hrms_branch_name, "company": tracora_comp}, "name")
	if not existing and frappe.db.exists("Tracora Branch", expected_name):
		existing = expected_name

	if existing:
		return existing

	if dry_run:
		return expected_name

	branch_doc = frappe.get_doc({
		"doctype": "Tracora Branch",
		"branch_name": hrms_branch_name,
		"company": tracora_comp,
		"source": "HRMS",
		"hrms_branch": hrms_branch_name
	})
	branch_doc.insert(ignore_permissions=True, ignore_links=True)
	return branch_doc.name


def _get_or_create_department(hrms_dept_name: str, company_name: str, dry_run: bool = False):
	"""Finds or creates a Tracora Department corresponding to HRMS Department under company."""
	if not hrms_dept_name or not company_name:
		return None

	tracora_comp = _get_or_create_company(company_name, dry_run=dry_run)
	comp_abbr = _get_company_abbr(company_name)
	expected_name = f"{hrms_dept_name} - {comp_abbr}"

	existing = frappe.db.get_value("Tracora Department", {"hrms_department": hrms_dept_name, "company": tracora_comp}, "name")
	if not existing and frappe.db.exists("Tracora Department", expected_name):
		existing = expected_name

	if existing:
		return existing

	if dry_run:
		return expected_name

	dept_doc = frappe.get_doc({
		"doctype": "Tracora Department",
		"department_name": hrms_dept_name,
		"company": tracora_comp,
		"source": "HRMS",
		"hrms_department": hrms_dept_name
	})
	dept_doc.insert(ignore_permissions=True, ignore_links=True)
	return dept_doc.name


def _has_outstanding_assets_or_seats(employee_name: str) -> bool:
	"""Checks if the employee holds active assets or software seats in Tracora."""
	if frappe.db.exists("DocType", "Tracora Asset"):
		count = frappe.db.count("Tracora Asset", filters={"assigned_to": employee_name, "status": ["not in", ["Retired", "Released"]]})
		if count > 0:
			return True

	if frappe.db.exists("DocType", "Tracora Licence Seat"):
		seat_count = frappe.db.count("Tracora Licence Seat", filters={"user": employee_name, "seat_status": "Active"})
		if seat_count > 0:
			return True

	return False


@safe_subscriber("on_employee_change", "Employee")
def on_employee_change(doc, method=None):
	"""HRMS Employee subscriber for after_insert and on_update."""
	apply_hrms_employee(doc, dry_run=False)


def apply_hrms_employee(doc, dry_run: bool = False) -> dict:
	"""Core sync logic for HRMS Employee record."""
	emp_code = doc.name
	hrms_company = doc.company
	mobile = getattr(doc, "cell_number", None) or getattr(doc, "mobile", None) or getattr(doc, "prefered_contact_email", "") or "0000000000"
	email = getattr(doc, "company_email", None) or getattr(doc, "prefered_email", None) or getattr(doc, "personal_email", None) or ""
	dob = str(doc.date_of_birth) if getattr(doc, "date_of_birth", None) else None
	perm_addr = getattr(doc, "permanent_address", None) or ""
	designation = getattr(doc, "designation", None) or ""
	hrms_status = getattr(doc, "status", "Active")

	# Determine company, branch, department
	tracora_company = _get_or_create_company(hrms_company, dry_run=dry_run) if hrms_company else None
	tracora_branch = _get_or_create_branch(doc.branch, tracora_company, dry_run=dry_run) if getattr(doc, "branch", None) and tracora_company else None
	tracora_dept = _get_or_create_department(doc.department, tracora_company, dry_run=dry_run) if getattr(doc, "department", None) and tracora_company else None
	is_incomplete = 1 if (not tracora_branch or not tracora_dept) else 0

	# Status calculation
	is_exited_hrms = hrms_status in ["Left", "Exited", "Inactive", "Relieved", "Resigned", "Suspended"]
	outstanding = _has_outstanding_assets_or_seats(emp_code)

	# Check if Tracora Employee already exists
	existing_name = frappe.db.get_value("Tracora Employee", {"hrms_employee": emp_code}, "name")
	if not existing_name and frappe.db.exists("Tracora Employee", emp_code):
		existing_name = emp_code

	if not existing_name:
		# Absent in Tracora -> Create with source = HRMS
		status = "Pending Clearance" if (is_exited_hrms and outstanding) else ("Exited" if is_exited_hrms else "Active")
		exit_date = (str(getattr(doc, "relieving_date", None) or getattr(doc, "leaving_date", None) or frappe.utils.today())) if is_exited_hrms else None
		exit_recorded_in = "HRMS" if is_exited_hrms else None

		if dry_run:
			return {"action": "created", "name": emp_code}

		new_emp = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": emp_code,
			"employee_name": doc.employee_name or emp_code,
			"designation": designation,
			"company": tracora_company,
			"branch": tracora_branch,
			"department": tracora_dept,
			"is_incomplete": is_incomplete,
			"mobile": mobile,
			"email": email,
			"date_of_birth": dob,
			"permanent_address": perm_addr,
			"status": status,
			"exit_date": exit_date,
			"exit_recorded_in": exit_recorded_in,
			"source": "HRMS",
			"hrms_employee": emp_code
		})
		new_emp.insert(ignore_permissions=True, ignore_links=True)
		return {"action": "created", "name": emp_code}

	# Existing record found
	tracora_emp = frappe.get_doc("Tracora Employee", existing_name)

	if tracora_emp.source == "HRMS":
		# Update HRMS-owned fields only. Aadhaar stays untouched (Rule 9a).
		if is_exited_hrms:
			tracora_emp.status = "Pending Clearance" if outstanding else "Exited"
			tracora_emp.exit_date = str(getattr(doc, "relieving_date", None) or getattr(doc, "leaving_date", None) or tracora_emp.exit_date or frappe.utils.today())
			tracora_emp.exit_recorded_in = "HRMS"
		else:
			# Reversal check: if active in HRMS and was exited via HRMS, restore to Active
			if tracora_emp.status in ["Exited", "Pending Clearance"] and tracora_emp.exit_recorded_in == "HRMS":
				tracora_emp.status = "Active"
				tracora_emp.exit_date = None
				tracora_emp.exit_recorded_in = None

		tracora_emp.employee_name = doc.employee_name or tracora_emp.employee_name
		tracora_emp.designation = designation
		tracora_emp.company = tracora_company
		tracora_emp.branch = tracora_branch
		tracora_emp.department = tracora_dept
		tracora_emp.is_incomplete = is_incomplete
		tracora_emp.mobile = mobile
		tracora_emp.email = email
		tracora_emp.date_of_birth = dob
		tracora_emp.permanent_address = perm_addr
		tracora_emp.hrms_employee = emp_code

		if dry_run:
			return {"action": "updated", "name": existing_name}

		tracora_emp.save(ignore_permissions=True)
		return {"action": "updated", "name": existing_name}

	elif tracora_emp.source == "Tracora":
		# Existing manual record: compare values of HRMS-owned fields
		hrms_vals = {
			"employee_name": doc.employee_name or "",
			"company": tracora_company or "",
			"mobile": mobile,
			"email": email or "",
			"date_of_birth": dob or "",
			"permanent_address": perm_addr or ""
		}
		tracora_vals = {
			"employee_name": tracora_emp.employee_name or "",
			"company": tracora_emp.company or "",
			"mobile": tracora_emp.mobile or "",
			"email": tracora_emp.email or "",
			"date_of_birth": str(tracora_emp.date_of_birth) if tracora_emp.date_of_birth else "",
			"permanent_address": tracora_emp.permanent_address or ""
		}

		differing = [k for k, v in hrms_vals.items() if v != tracora_vals.get(k)]

		if not differing:
			# Matching values -> attach reference and flip source
			if dry_run:
				return {"action": "linked", "name": existing_name}
			tracora_emp.hrms_employee = emp_code
			tracora_emp.source = "HRMS"
			tracora_emp.save(ignore_permissions=True)
			return {"action": "linked", "name": existing_name}
		else:
			# Differing values -> write nothing, raise Tracora Sync Conflict (FR-56)
			if dry_run:
				return {"action": "conflict", "name": existing_name, "differing": differing}

			# Create conflict record if not already open
			existing_conflict = frappe.db.get_value(
				"Tracora Sync Conflict",
				{"reference_key": existing_name, "conflict_status": "Open"},
				"name"
			)
			if not existing_conflict:
				frappe.get_doc({
					"doctype": "Tracora Sync Conflict",
					"reference_doctype": "Tracora Employee",
					"reference_key": existing_name,
					"conflict_type": "Value mismatch",
					"hrms_reference": emp_code,
					"differing_fields": ", ".join(differing),
					"hrms_values": json.dumps(hrms_vals, indent=2),
					"tracora_values": json.dumps(tracora_vals, indent=2),
					"conflict_status": "Open"
				}).insert(ignore_permissions=True, ignore_links=True)

			return {"action": "conflict", "name": existing_name, "differing": differing}

	return {"action": "skipped", "name": emp_code}


@safe_subscriber("on_employee_rename", "Employee")
def on_employee_rename(doc, method=None, old=None, new=None, *args, **kwargs):
	"""HRMS Employee rename subscriber (after_rename)."""
	old_code = old or kwargs.get("old_name") or kwargs.get("old") or (args[0] if len(args) > 0 else None)
	new_code = new or kwargs.get("new_name") or kwargs.get("new") or (args[1] if len(args) > 1 else None) or getattr(doc, "name", None)
	if not old_code or not new_code or old_code == new_code:
		return

	# Match Tracora Employee by hrms_employee
	tracora_emp_name = frappe.db.get_value("Tracora Employee", {"hrms_employee": old_code}, "name")
	if not tracora_emp_name and frappe.db.exists("Tracora Employee", old_code):
		tracora_emp_name = old_code

	if tracora_emp_name:
		if tracora_emp_name != new_code:
			frappe.rename_doc("Tracora Employee", tracora_emp_name, new_code, force=True)
		# Update fields
		frappe.db.set_value("Tracora Employee", new_code, {"employee_code": new_code, "hrms_employee": new_code}, update_modified=False)


@safe_subscriber("on_hrms_delete", "Employee")
def on_hrms_delete(doc, method=None):
	"""HRMS Employee delete subscriber (on_trash). Keep record, clear reference, flip source."""
	emp_code = getattr(doc, "name", None)
	if not emp_code:
		return

	tracora_emp_name = frappe.db.get_value("Tracora Employee", {"hrms_employee": emp_code}, "name")
	if not tracora_emp_name and frappe.db.exists("Tracora Employee", emp_code):
		tracora_emp_name = emp_code

	if tracora_emp_name:
		frappe.db.set_value(
			"Tracora Employee",
			tracora_emp_name,
			{"hrms_employee": None, "source": "Tracora"},
			update_modified=False
		)


@safe_subscriber("on_company_change", "Company")
def on_company_change(doc, method=None):
	"""HRMS Company subscriber for on_update."""
	_get_or_create_company(doc.name, dry_run=False)


@safe_subscriber("on_branch_change", "Branch")
def on_branch_change(doc, method=None):
	"""HRMS Branch subscriber for on_update."""
	for comp in frappe.get_all("Tracora Company", filters={"source": "HRMS"}, pluck="name"):
		_get_or_create_branch(doc.name, comp, dry_run=False)


@safe_subscriber("on_branch_rename", "Branch")
def on_branch_rename(doc, method=None, old=None, new=None, *args, **kwargs):
	"""HRMS Branch rename subscriber."""
	old_name = old or kwargs.get("old_name") or kwargs.get("old") or (args[0] if len(args) > 0 else None)
	new_name = new or kwargs.get("new_name") or kwargs.get("new") or (args[1] if len(args) > 1 else None) or getattr(doc, "name", None)
	if not old_name or not new_name or old_name == new_name:
		return

	branches = frappe.get_all("Tracora Branch", filters={"hrms_branch": old_name}, fields=["name", "company"])
	for b in branches:
		comp_abbr = _get_company_abbr(b.company)
		new_branch_docname = f"{new_name} - {comp_abbr}"
		if b.name != new_branch_docname:
			frappe.rename_doc("Tracora Branch", b.name, new_branch_docname, force=True)
		frappe.db.set_value("Tracora Branch", new_branch_docname, {"branch_name": new_name, "hrms_branch": new_name}, update_modified=False)


@safe_subscriber("on_department_change", "Department")
def on_department_change(doc, method=None):
	"""HRMS Department subscriber for on_update."""
	hrms_comp = getattr(doc, "company", None)
	if hrms_comp:
		_get_or_create_department(doc.name, hrms_comp, dry_run=False)
	else:
		for comp in frappe.get_all("Tracora Company", filters={"source": "HRMS"}, pluck="name"):
			_get_or_create_department(doc.name, comp, dry_run=False)


@frappe.whitelist(methods=["POST"])
def bulk_import(dry_run: bool = True):
	"""Whitelisted bulk import tool for one-time seeding from HRMS. Super Admin only."""
	frappe.only_for("Tracora Super Admin")
	dry_run = frappe.parse_json(dry_run) if isinstance(dry_run, str) else bool(dry_run)

	results = {
		"dry_run": dry_run,
		"created": {"Company": 0, "Branch": 0, "Department": 0, "Employee": 0},
		"updated": {"Employee": 0},
		"linked": {"Employee": 0},
		"conflicts": [],
		"skipped": 0
	}

	if not frappe.db.exists("DocType", "Employee"):
		return results

	# 1. Companies
	if frappe.db.exists("DocType", "Company"):
		for c in frappe.get_all("Company", fields=["name"]):
			exists = frappe.db.exists("Tracora Company", {"hrms_company": c.name}) or frappe.db.exists("Tracora Company", c.name)
			if not exists:
				_get_or_create_company(c.name, dry_run=dry_run)
				results["created"]["Company"] += 1

	# 2. Branches
	if frappe.db.exists("DocType", "Branch"):
		companies = frappe.get_all("Tracora Company", pluck="name")
		for b in frappe.get_all("Branch", fields=["name"]):
			for comp in companies:
				comp_abbr = _get_company_abbr(comp)
				expected = f"{b.name} - {comp_abbr}"
				exists = frappe.db.exists("Tracora Branch", expected) or frappe.db.exists("Tracora Branch", {"hrms_branch": b.name, "company": comp})
				if not exists:
					_get_or_create_branch(b.name, comp, dry_run=dry_run)
					results["created"]["Branch"] += 1

	# 3. Departments
	if frappe.db.exists("DocType", "Department"):
		for d in frappe.get_all("Department", fields=["name", "company"]):
			d_comp = d.company
			target_comps = [d_comp] if d_comp else frappe.get_all("Tracora Company", pluck="name")
			for comp in target_comps:
				if not comp:
					continue
				comp_abbr = _get_company_abbr(comp)
				expected = f"{d.name} - {comp_abbr}"
				exists = frappe.db.exists("Tracora Department", expected) or frappe.db.exists("Tracora Department", {"hrms_department": d.name, "company": comp})
				if not exists:
					_get_or_create_department(d.name, comp, dry_run=dry_run)
					results["created"]["Department"] += 1

	# 4. Employees
	for emp_row in frappe.get_all("Employee", fields=["name"]):
		hrms_emp = frappe.get_doc("Employee", emp_row.name)
		res = apply_hrms_employee(hrms_emp, dry_run=dry_run)
		action = res.get("action")
		if action == "created":
			results["created"]["Employee"] += 1
		elif action == "updated":
			results["updated"]["Employee"] += 1
		elif action == "linked":
			results["linked"]["Employee"] += 1
		elif action == "conflict":
			results["conflicts"].append({"employee": emp_row.name, "differing": res.get("differing", [])})
		else:
			results["skipped"] += 1

	return results
