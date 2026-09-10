# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import (
	date_diff,
	getdate,
	now_datetime,
	today,
	format_date,
	time_diff_in_hours,
)


def get_active_recipients():
	"""
	Resolves active recipients holding Tracora Super Admin or Tracora Admin roles.
	Filters explicitly for enabled = 1 and user_type = 'System User'.
	"""
	admin_users = frappe.get_all(
		"Has Role",
		filters={
			"role": ["in", ["Tracora Super Admin", "Tracora Admin"]],
			"parenttype": "User",
		},
		pluck="parent",
		distinct=True,
	)
	if not admin_users:
		return []

	active_recipients = frappe.get_all(
		"User",
		filters={
			"name": ["in", admin_users],
			"enabled": 1,
			"user_type": "System User",
		},
		pluck="email",
	)
	return [r for r in active_recipients if r and str(r).strip()]


def parse_lead_days(settings_doc):
	"""
	Returns set of lead day integers from settings.
	"""
	raw = (settings_doc.reminder_lead_days or "30,15,7,2,1,0").strip()
	lead_days = set()
	for part in raw.split(","):
		part = part.strip()
		if part.isdigit():
			lead_days.add(int(part))
	return lead_days


def get_licence_seats_summary(licence_name):
	"""
	Returns formatted seats summary for reminder email body.
	"""
	seats = frappe.get_all(
		"Tracora Licence Seat",
		filters={"parent": licence_name, "parenttype": "Tracora Software Licence"},
		fields=["name", "user", "device", "seat_status"],
	)
	if not seats:
		return "<p><i>No seats currently allocated.</i></p>"

	rows = []
	for s in seats:
		user_display = s.user or "Unassigned"
		device_display = s.device or "N/A"
		rows.append(
			f"<tr>"
			f"<td style='padding: 6px 10px; border: 1px solid #ddd;'>{frappe.utils.escape_html(user_display)}</td>"
			f"<td style='padding: 6px 10px; border: 1px solid #ddd;'>{frappe.utils.escape_html(device_display)}</td>"
			f"<td style='padding: 6px 10px; border: 1px solid #ddd;'>{frappe.utils.escape_html(s.seat_status)}</td>"
			f"</tr>"
		)

	table_html = f"""
	<table style="border-collapse: collapse; width: 100%; max-width: 600px; margin-top: 8px; font-size: 13px;">
		<thead>
			<tr style="background-color: #f7f7f7; text-align: left;">
				<th style="padding: 6px 10px; border: 1px solid #ddd;">User</th>
				<th style="padding: 6px 10px; border: 1px solid #ddd;">Device</th>
				<th style="padding: 6px 10px; border: 1px solid #ddd;">Seat Status</th>
			</tr>
		</thead>
		<tbody>
			{''.join(rows)}
		</tbody>
	</table>
	"""
	return table_html


def dispatch_reminder_notice(lic, reminder_type, due_date, days_before, recipient):
	"""
	Sends individual email and records Tracora Reminder Log row.
	Per LLD & plan: professional tone, no marketing, no filler.
	"""
	sw_name = lic.software_name or "Software Licence"
	lic_label = f"{lic.licence_name} ({lic.name})" if lic.licence_name else lic.name
	due_str = format_date(due_date)

	if reminder_type == "Licence Expiry":
		if days_before < 0:
			subject = f"Licence OVERDUE: {sw_name} ({due_str})"
			heading = f"Licence {sw_name} ({lic_label}) expired on {due_str}."
		elif days_before == 0:
			subject = f"Licence expiring TODAY: {sw_name} ({due_str})"
			heading = f"Licence {sw_name} ({lic_label}) expires today ({due_str})."
		else:
			subject = f"Licence expiring in {days_before} days: {sw_name} ({due_str})"
			heading = f"Licence {sw_name} ({lic_label}) expires in {days_before} days ({due_str})."
	else:  # Licence Renewal
		if days_before == 0:
			subject = f"Licence renewal due TODAY: {sw_name} ({due_str})"
			heading = f"Licence {sw_name} ({lic_label}) renewal is due today ({due_str})."
		else:
			subject = f"Licence renewal in {days_before} days: {sw_name} ({due_str})"
			heading = f"Licence {sw_name} ({lic_label}) renewal is due in {days_before} days ({due_str})."

	site_url = frappe.utils.get_url()
	licence_link = f"{site_url}/app/tracora-software-licence/{lic.name}"
	seats_table = get_licence_seats_summary(lic.name)

	body = f"""
	<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.5;">
		<p><b>{heading}</b></p>
		<p><b>Record:</b> <a href="{licence_link}">{lic.name}</a><br>
		<b>Software:</b> {frappe.utils.escape_html(sw_name)}<br>
		<b>Due Date:</b> {due_str}<br>
		<b>Status:</b> {frappe.utils.escape_html(lic.licence_status or 'Active')}</p>

		<p><b>Allocated Seats:</b></p>
		{seats_table}

		<p style="margin-top: 16px;">
			<a href="{licence_link}" style="background-color: #2b6cb0; color: #ffffff; padding: 8px 14px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: 500;">View Licence in Tracora</a>
		</p>
	</div>
	"""

	delivery_status = "Sent"
	error_msg = None
	try:
		frappe.sendmail(
			recipients=[recipient],
			subject=subject,
			message=body,
			reference_doctype="Tracora Software Licence",
			reference_name=lic.name,
			now=False,
		)
	except Exception as e:
		delivery_status = "Failed"
		error_msg = str(e)
		frappe.logger().error(f"Failed to dispatch reminder to {recipient} for {lic.name}: {error_msg}")

	log_doc = frappe.get_doc({
		"doctype": "Tracora Reminder Log",
		"reference_doctype": "Tracora Software Licence",
		"reference_name": lic.name,
		"reminder_type": reminder_type,
		"due_date": due_date,
		"days_before": days_before,
		"recipient": recipient,
		"sent_on": now_datetime(),
		"delivery_status": delivery_status,
		"error_message": error_msg,
	})
	log_doc.insert(ignore_permissions=True)
	return log_doc


def run_daily_reminders():
	"""
	FR-25 to FR-29, FR-63 to FR-65, FR-89, FR-90.
	Registered in scheduler_events['daily'].
	1. Blank date -> skip.
	2. Overdue past expiry -> send exactly one overdue notice (days_before = -1).
	3. Upcoming milestones in reminder_lead_days -> send notice (days_before = diff).
	4. Individual email and log row per recipient.
	5. Idempotent: existing log row suppresses duplicate.
	6. Stamps Tracora Settings.last_reminder_run = now().
	"""
	settings = frappe.get_single("Tracora Settings")
	lead_days = parse_lead_days(settings)
	recipients = get_active_recipients()

	if not recipients:
		frappe.logger().warning("run_daily_reminders: No active Tracora administrator recipients found.")
		settings.last_reminder_run = now_datetime()
		settings.flags.ignore_permissions = True
		settings.save(ignore_permissions=True)
		frappe.db.commit()
		return

	licences = frappe.get_all(
		"Tracora Software Licence",
		fields=[
			"name",
			"software_name",
			"licence_name",
			"licence_expiry_date",
			"next_renewal_date",
			"licence_status",
		],
	)

	today_date = getdate(today())

	for lic in licences:
		# --- Check 1: licence_expiry_date ---
		if lic.licence_expiry_date:
			expiry_date = getdate(lic.licence_expiry_date)
			diff = date_diff(expiry_date, today_date)

			if diff < 0:
				# FR-89: Overdue past expiry -> exactly one overdue notice
				for rec in recipients:
					already_logged = frappe.db.exists(
						"Tracora Reminder Log",
						{
							"reference_doctype": "Tracora Software Licence",
							"reference_name": lic.name,
							"reminder_type": "Licence Expiry",
							"due_date": expiry_date,
							"days_before": -1,
							"recipient": rec,
						},
					)
					if not already_logged:
						dispatch_reminder_notice(lic, "Licence Expiry", expiry_date, -1, rec)

			elif diff in lead_days:
				# Upcoming expiry milestone
				for rec in recipients:
					already_logged = frappe.db.exists(
						"Tracora Reminder Log",
						{
							"reference_doctype": "Tracora Software Licence",
							"reference_name": lic.name,
							"reminder_type": "Licence Expiry",
							"due_date": expiry_date,
							"days_before": diff,
							"recipient": rec,
						},
					)
					if not already_logged:
						dispatch_reminder_notice(lic, "Licence Expiry", expiry_date, diff, rec)

		# --- Check 2: next_renewal_date ---
		if lic.next_renewal_date:
			renewal_date = getdate(lic.next_renewal_date)
			diff = date_diff(renewal_date, today_date)

			# Upcoming renewal milestone (diff >= 0 defensive guard)
			if diff in lead_days and diff >= 0:
				for rec in recipients:
					already_logged = frappe.db.exists(
						"Tracora Reminder Log",
						{
							"reference_doctype": "Tracora Software Licence",
							"reference_name": lic.name,
							"reminder_type": "Licence Renewal",
							"due_date": renewal_date,
							"days_before": diff,
							"recipient": rec,
						},
					)
					if not already_logged:
						dispatch_reminder_notice(lic, "Licence Renewal", renewal_date, diff, rec)

	# Stamp finish timestamp
	settings.last_reminder_run = now_datetime()
	settings.flags.ignore_permissions = True
	settings.save(ignore_permissions=True)
	frappe.db.commit()


@frappe.whitelist()
def check_scheduler_health():
	"""
	FR-90: Returns scheduler health status for Tracora workspace banner.
	Stale if last_reminder_run > 48 hours ago or missing, or if no active recipients exist.
	"""
	settings = frappe.get_single("Tracora Settings")
	last_run = settings.last_reminder_run
	recipients = get_active_recipients()

	is_stale = False
	stale_message = None
	days_ago = None

	if not last_run:
		is_stale = True
		stale_message = _("Reminders have never run. Scheduled background jobs may be stopped.")
	else:
		hours = time_diff_in_hours(now_datetime(), last_run)
		if hours > 48:
			is_stale = True
			days_ago = max(1, int(round(hours / 24.0)))
			stale_message = _("Reminders last ran {0} days ago. Scheduled background jobs may be stopped.").format(days_ago)

	no_recipients = len(recipients) == 0
	recipient_message = None
	if no_recipients:
		recipient_message = _("No active administrator users hold reminder roles. Scheduled background jobs may not dispatch notifications.")

	return {
		"is_stale": is_stale,
		"stale_message": stale_message,
		"days_ago": days_ago,
		"last_run": str(last_run) if last_run else None,
		"no_recipients": no_recipients,
		"recipient_message": recipient_message,
	}
