import frappe


def execute():
	# 1. Update any existing Flagged seats to Released
	frappe.db.sql("""
		UPDATE `tabTracora Licence Seat`
		SET seat_status = 'Released'
		WHERE seat_status = 'Flagged'
	""")

	# 2. Recalculate licence_status for licences whose active seats may have changed
	licences = frappe.get_all("Tracora Software Licence", fields=["name", "licence_status", "licence_expiry_date"])
	for lic in licences:
		active_count = frappe.db.count("Tracora Licence Seat", filters={"parent": lic.name, "seat_status": "Active"})
		new_status = lic.licence_status
		if active_count == 0:
			new_status = "Unassigned"
		elif lic.licence_expiry_date and frappe.utils.getdate(lic.licence_expiry_date) < frappe.utils.getdate(frappe.utils.today()):
			new_status = "Expired"
		else:
			new_status = "Active"

		if new_status != lic.licence_status:
			frappe.db.set_value("Tracora Software Licence", lic.name, "licence_status", new_status)
