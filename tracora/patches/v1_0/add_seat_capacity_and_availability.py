import frappe


def execute():
	"""Backfill total_seats, allocated_seats, and seat_availability for existing software licences."""
	licences = frappe.get_all("Tracora Software Licence", fields=["name", "total_seats"])
	for lic in licences:
		active_count = frappe.db.count(
			"Tracora Licence Seat",
			filters={"parent": lic.name, "seat_status": "Active"}
		)
		total = lic.total_seats or max(1, active_count)
		availability = "Depleted" if active_count >= total else "Available"

		frappe.db.set_value(
			"Tracora Software Licence",
			lic.name,
			{
				"total_seats": total,
				"allocated_seats": active_count,
				"seat_availability": availability
			},
			update_modified=False
		)

	frappe.db.commit()
