# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today
from tracora.licences.roll_forward import calculate_next_renewal


class TracoraSoftwareLicence(Document):
	def validate(self):
		# Validate total_seats capacity (minimum 1) if explicitly provided
		if self.total_seats is not None and self.total_seats < 1:
			frappe.throw(_("Total Seats must be at least 1."), frappe.ValidationError)

		# FR-21, FR-85: Seat validation according to licence_type
		seen_pairs = set()
		for seat in self.seats or []:
			if self.licence_type == "User licence":
				if not seat.user:
					frappe.throw(
						_("User is required for each seat on a User licence (FR-21, FR-85). Row #{0}").format(seat.idx),
						frappe.ValidationError
					)
				if not seat.device:
					frappe.throw(
						_("Device is required for each seat on a User licence (FR-21). Row #{0}").format(seat.idx),
						frappe.ValidationError
					)
			elif self.licence_type == "Device licence":
				if not seat.device:
					frappe.throw(
						_("Device is required for each seat on a Device licence (FR-21). Row #{0}").format(seat.idx),
						frappe.ValidationError
					)

			# FR-21: The same user and device cannot appear twice on one licence
			pair_key = (seat.user or "", seat.device)
			if pair_key in seen_pairs:
				user_label = seat.user or _("Unassigned user")
				frappe.throw(
					_("Duplicate user and device pair ({0}, {1}) on licence '{2}' (FR-21).").format(
						user_label, seat.device, self.licence_name or self.software_name or self.name
					),
					frappe.ValidationError
				)
			seen_pairs.add(pair_key)

		# Count currently active allocated seats
		active_seats = [s for s in (self.seats or []) if s.seat_status == "Active"]
		self.allocated_seats = len(active_seats)

		# Auto-initialize total_seats if not specified (e.g. programmatic creation/imports)
		if self.total_seats is None:
			self.total_seats = max(1, self.allocated_seats)

		# Hard block if active allocated seats exceed total_seats capacity
		if self.total_seats and self.allocated_seats > self.total_seats:
			frappe.throw(
				_("Cannot assign {0} active seats: Licence '{1}' capacity is depleted (Total Seats: {2}).").format(
					self.allocated_seats, self.licence_name or self.software_name or self.name, self.total_seats
				),
				frappe.ValidationError
			)

		# Real-time seat availability calculation
		if self.total_seats and self.allocated_seats >= self.total_seats:
			self.seat_availability = "Depleted"
		else:
			self.seat_availability = "Available"

		# Auto-calculate next_renewal_date from licence_start_date + renewal_cycle
		if self.licence_start_date and self.renewal_cycle:
			self.next_renewal_date = calculate_next_renewal(self.licence_start_date, self.renewal_cycle)
		elif not self.licence_start_date:
			self.next_renewal_date = None

		# FR-20, FR-86: Compute licence_status automatically (not by hand)
		if not active_seats:
			self.licence_status = "Unassigned"
		elif self.licence_expiry_date and getdate(self.licence_expiry_date) < getdate(today()):
			self.licence_status = "Expired"
		else:
			self.licence_status = "Active"
