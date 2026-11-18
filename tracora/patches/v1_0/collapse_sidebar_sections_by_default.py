import frappe


def execute():
	# Update database directly for Workspace Sidebar 'Tracora' items
	frappe.db.sql("""
		UPDATE `tabWorkspace Sidebar Item`
		SET `keep_closed` = 1
		WHERE parent = 'Tracora' AND type = 'Section Break'
	""")

	# Also update the Workspace Sidebar doc if present
	if frappe.db.exists("Workspace Sidebar", "Tracora"):
		sidebar = frappe.get_doc("Workspace Sidebar", "Tracora")
		for item in sidebar.items:
			if item.type == "Section Break":
				item.keep_closed = 1
		sidebar.save(ignore_permissions=True)

	frappe.clear_cache()
