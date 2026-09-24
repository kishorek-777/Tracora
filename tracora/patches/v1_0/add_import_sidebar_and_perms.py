import frappe


def execute():
	# 1. Ensure Import Data item exists in tabWorkspace Sidebar Item for Tracora
	sidebar = frappe.get_doc("Workspace Sidebar", "Tracora")
	sidebar_items = [it.label for it in sidebar.items]
	if "Import Data" not in sidebar_items:
		# Find index of Settings
		idx = len(sidebar.items)
		for i, it in enumerate(sidebar.items):
			if it.label == "Settings":
				idx = i + 1
				break
		sidebar.append("items", {
			"label": "Import Data",
			"type": "Link",
			"link_type": "DocType",
			"link_to": "Data Import",
			"icon": "upload",
			"indent": 0,
			"collapsible": 1,
			"keep_closed": 0,
			"show_arrow": 0
		})
		sidebar.save(ignore_permissions=True)

	# 2. Update tabDocPerm in database to grant import permission to admin roles
	target_doctypes = [
		"Tracora Asset",
		"Tracora Employee",
		"Tracora Software Licence",
		"Tracora Company",
		"Tracora Branch",
		"Tracora Department",
		"Tracora Location",
		"Tracora Maintenance Log",
	]

	for dt in target_doctypes:
		frappe.db.sql("""
			UPDATE `tabDocPerm`
			SET `import` = 1
			WHERE parent = %s AND role IN ('Tracora Super Admin', 'Tracora Admin', 'System Manager')
		""", (dt,))

	# 3. Enable allow_import on target DocTypes in tabDocType
	for dt in target_doctypes:
		frappe.db.set_value("DocType", dt, "allow_import", 1)
