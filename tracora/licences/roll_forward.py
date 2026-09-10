# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_months, getdate, today


def advance_date_by_cycle(base_date, cycle: str):
	"""Advances base_date according to renewal_cycle (FR-23)."""
	if not base_date:
		return None
	b_date = getdate(base_date)
	cycle = (cycle or "").strip()
	if cycle == "Monthly":
		return add_months(b_date, 1)
	elif cycle == "Quarterly":
		return add_months(b_date, 3)
	elif cycle == "Half-yearly":
		return add_months(b_date, 6)
	elif cycle == "Yearly":
		return add_months(b_date, 12)
	return b_date


def calculate_next_renewal(start_date, cycle, reference_date=None):
	"""Given when the licence started and its renewal cycle, return the
	next renewal checkpoint on or after reference_date (defaults to today)."""
	if not start_date or cycle == "One-time":
		return None
	reference_date = getdate(reference_date or today())
	next_date = getdate(start_date)
	while next_date < reference_date:
		advanced = advance_date_by_cycle(next_date, cycle)
		if advanced <= next_date:
			break
		next_date = advanced
	return next_date
