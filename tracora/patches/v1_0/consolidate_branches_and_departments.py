# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""
	Consolidate Tracora Branch and Tracora Department records from company-qualified
	names ({name} - {company_abbr}) to clean global names ({name}).
	Safely re-links all Tracora Employee and Tracora Asset foreign keys.
	"""
	# 1. Consolidate Tracora Branch
	if frappe.db.exists("DocType", "Tracora Branch"):
		all_branches = frappe.get_all(
			"Tracora Branch",
			fields=["name", "branch_name", "company", "source", "hrms_branch"]
		)

		branches_by_base = {}
		for b in all_branches:
			raw_name = b.branch_name or b.name
			base = raw_name.split(" - ")[0].strip() if " - " in raw_name else raw_name.strip()
			branches_by_base.setdefault(base, []).append(b)

		for base_name, branch_list in branches_by_base.items():
			if not base_name:
				continue

			canonical_exists = frappe.db.exists("Tracora Branch", base_name)

			if not canonical_exists:
				first_b = branch_list[0]
				frappe.rename_doc("Tracora Branch", first_b.name, base_name, force=True, merge=False)
				branch_list = branch_list[1:]

			frappe.db.set_value(
				"Tracora Branch",
				base_name,
				{"branch_name": base_name, "company": None},
				update_modified=False
			)

			for dup in branch_list:
				if dup.name == base_name:
					continue

				if frappe.db.exists("Tracora Branch", dup.name):
					try:
						frappe.rename_doc("Tracora Branch", dup.name, base_name, force=True, merge=True)
					except Exception:
						# Direct fallback re-link and delete
						frappe.db.sql(
							"UPDATE `tabTracora Employee` SET `branch` = %s WHERE `branch` = %s",
							(base_name, dup.name)
						)
						frappe.db.sql(
							"UPDATE `tabTracora Asset` SET `branch` = %s WHERE `branch` = %s",
							(base_name, dup.name)
						)
						frappe.delete_doc("Tracora Branch", dup.name, force=True, ignore_permissions=True)

	# 2. Consolidate Tracora Department
	if frappe.db.exists("DocType", "Tracora Department"):
		all_depts = frappe.get_all(
			"Tracora Department",
			fields=["name", "department_name", "company", "source", "hrms_department"]
		)

		depts_by_base = {}
		for d in all_depts:
			raw_name = d.department_name or d.name
			base = raw_name.split(" - ")[0].strip() if " - " in raw_name else raw_name.strip()
			depts_by_base.setdefault(base, []).append(d)

		for base_name, dept_list in depts_by_base.items():
			if not base_name:
				continue

			canonical_exists = frappe.db.exists("Tracora Department", base_name)

			if not canonical_exists:
				first_d = dept_list[0]
				frappe.rename_doc("Tracora Department", first_d.name, base_name, force=True, merge=False)
				dept_list = dept_list[1:]

			frappe.db.set_value(
				"Tracora Department",
				base_name,
				{"department_name": base_name, "company": None},
				update_modified=False
			)

			for dup in dept_list:
				if dup.name == base_name:
					continue

				if frappe.db.exists("Tracora Department", dup.name):
					try:
						frappe.rename_doc("Tracora Department", dup.name, base_name, force=True, merge=True)
					except Exception:
						frappe.db.sql(
							"UPDATE `tabTracora Employee` SET `department` = %s WHERE `department` = %s",
							(base_name, dup.name)
						)
						frappe.delete_doc("Tracora Department", dup.name, force=True, ignore_permissions=True)

	frappe.db.commit()

