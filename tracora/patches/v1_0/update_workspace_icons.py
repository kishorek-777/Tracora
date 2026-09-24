import frappe


def execute():
	# Update Workspace Sidebar Item icons to modern Lucide names supported in Frappe v16
	frappe.db.sql("""
		UPDATE `tabWorkspace Sidebar Item`
		SET icon = 'triangle-alert'
		WHERE label = 'Sync Conflicts' AND (icon = 'alert-triangle' OR icon IS NULL OR icon = '')
	""")

	frappe.db.sql("""
		UPDATE `tabWorkspace Sidebar Item`
		SET icon = 'chart-column'
		WHERE label = 'Reports' AND type = 'Link' AND (icon = 'bar-chart-2' OR icon IS NULL OR icon = '')
	""")

	# Update Desktop Icon
	frappe.db.sql("""
		UPDATE `tabDesktop Icon`
		SET icon = 'chart-column'
		WHERE name IN ('Reports', 'Tracora Reports') AND icon = 'bar-chart-2'
	""")

	# Update Workspace
	frappe.db.sql("""
		UPDATE `tabWorkspace`
		SET icon = 'chart-column'
		WHERE name = 'Tracora Reports' AND icon = 'bar-chart-2'
	""")
