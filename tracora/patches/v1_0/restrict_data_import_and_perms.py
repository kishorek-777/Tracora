import frappe
from frappe.permissions import add_permission, update_permission_property, setup_custom_perms


def execute():
	# 1. Setup Custom DocPerm for Data Import
	setup_custom_perms("Data Import")

	# Grant read, write, create, export (no delete) to Tracora Admin & Super Admin
	for role in ["Tracora Admin", "Tracora Super Admin"]:
		if not frappe.db.exists("Custom DocPerm", {"parent": "Data Import", "role": role, "permlevel": 0}):
			add_permission("Data Import", role, permlevel=0, ptype="read")

		update_permission_property("Data Import", role, 0, "write", 1)
		update_permission_property("Data Import", role, 0, "create", 1)
		update_permission_property("Data Import", role, 0, "export", 1)
		update_permission_property("Data Import", role, 0, "delete", 0)

	# 2. Update target doctypes allow_import and tabDocPerm
	allowed_doctypes = ["Tracora Asset", "Tracora Software Licence"]
	disallowed_doctypes = [
		"Tracora Employee",
		"Tracora Company",
		"Tracora Branch",
		"Tracora Department",
		"Tracora Location",
		"Tracora Maintenance Log",
	]

	for dt in allowed_doctypes:
		frappe.db.set_value("DocType", dt, "allow_import", 1)
		for role in ["Tracora Admin", "Tracora Super Admin"]:
			frappe.db.sql(
				"UPDATE `tabDocPerm` SET `import` = 1 WHERE parent = %s AND role = %s",
				(dt, role),
			)
			frappe.db.sql(
				"UPDATE `tabCustom DocPerm` SET `import` = 1 WHERE parent = %s AND role = %s",
				(dt, role),
			)

	for dt in disallowed_doctypes:
		frappe.db.set_value("DocType", dt, "allow_import", 0)
		for role in ["Tracora Admin", "Tracora Super Admin"]:
			frappe.db.sql(
				"UPDATE `tabDocPerm` SET `import` = 0 WHERE parent = %s AND role = %s",
				(dt, role),
			)
			frappe.db.sql(
				"UPDATE `tabCustom DocPerm` SET `import` = 0 WHERE parent = %s AND role = %s",
				(dt, role),
			)

	frappe.clear_cache()
