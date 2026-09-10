# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today
from tracora.licences.roll_forward import calculate_next_renewal


def mark_expired_licences():
	"""
	Scheduled job (daily/hourly) as specified in docs/LLD.md scheduler events.
	Queries licences whose expiry date has passed and sets licence_status = 'Expired'.
	Indexed server-side filter avoids scanning already-expired licences.
	"""
	if not frappe.db.exists("DocType", "Tracora Software Licence"):
		return 0

	current_date = today()
	expired_licences = frappe.db.get_all(
		"Tracora Software Licence",
		filters={
			"licence_status": "Active",
			"licence_expiry_date": ["<", current_date]
		},
		pluck="name"
	)

	for name in expired_licences:
		frappe.db.set_value("Tracora Software Licence", name, "licence_status", "Expired")

	if expired_licences:
		frappe.db.commit()

	return len(expired_licences)


def recalculate_next_renewal_dates():
	"""Daily job. Recomputes next_renewal_date for every licence with a
	licence_start_date set. Also updates last_renewed_on if the computed
	date has advanced past the previously stored value (i.e., a renewal
	checkpoint was just crossed)."""
	if not frappe.db.exists("DocType", "Tracora Software Licence"):
		return 0

	licences = frappe.get_all(
		"Tracora Software Licence",
		filters={"licence_start_date": ["is", "set"]},
		fields=["name", "licence_start_date", "renewal_cycle", "next_renewal_date"]
	)
	updated_count = 0
	for lic in licences:
		new_date = calculate_next_renewal(lic.licence_start_date, lic.renewal_cycle)
		if new_date != lic.next_renewal_date:
			update = {"next_renewal_date": new_date}
			if lic.next_renewal_date and new_date > lic.next_renewal_date:
				update["last_renewed_on"] = today()
			frappe.db.set_value("Tracora Software Licence", lic.name, update)
			updated_count += 1

	if updated_count:
		frappe.db.commit()

	return updated_count
