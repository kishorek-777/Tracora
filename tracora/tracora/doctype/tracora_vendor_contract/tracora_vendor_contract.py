# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	add_months,
	add_years,
	date_diff,
	getdate,
	now_datetime,
	today,
	validate_email_address,
)


class TracoraVendorContract(Document):
	def validate(self):
		if not self.contract_title or not self.contract_title.strip():
			frappe.throw(_("Contract / Service Title is mandatory."), frappe.MandatoryError)
		self.contract_title = self.contract_title.strip()

		# 1. Validate Vendor
		if self.vendor:
			vendor_status = frappe.db.get_value("Tracora Vendor", self.vendor, "status")
			if not vendor_status:
				frappe.throw(_("Vendor '{0}' does not exist.").format(self.vendor), frappe.DoesNotExistError)
			if vendor_status != "Active":
				frappe.throw(
					_("Vendor '{0}' is currently marked as {1}. Cannot link contracts to inactive or blacklisted vendors.").format(
						self.vendor, vendor_status
					),
					frappe.ValidationError,
				)

		# 2. Currency fallback
		if not self.currency:
			self.currency = frappe.db.get_default("currency") or "INR"

		# 3. Additional recipients email validation
		if self.additional_recipients:
			emails = [e.strip() for e in self.additional_recipients.replace("\n", ",").split(",") if e.strip()]
			for email in emails:
				validate_email_address(email, throw=True)

		# 4. Validate payment history rows
		for row in self.get("payment_history", []):
			if not row.currency:
				row.currency = self.currency
			if not row.amount_paid or float(row.amount_paid) <= 0:
				frappe.throw(_("Payment amount must be greater than zero."), frappe.ValidationError)
			if not row.recorded_by:
				row.recorded_by = frappe.session.user
			if not row.recorded_on:
				row.recorded_on = now_datetime()

		# 5. Status calculation
		self._update_renewal_status()

	def _update_renewal_status(self):
		if self.renewal_status in ["Completed / One-off", "Closed / Terminated"]:
			return

		if self.renewal_frequency == "One-off / Non-recurring":
			if len(self.get("payment_history", [])) > 0:
				self.renewal_status = "Completed / One-off"
				self.next_renewal_date = None
			return

		if self.next_renewal_date:
			due = getdate(self.next_renewal_date)
			current = getdate(today())
			diff = date_diff(due, current)

			if diff < 0:
				self.renewal_status = "Overdue"
			elif diff <= 15:
				self.renewal_status = "Due Soon"
			else:
				self.renewal_status = "Upcoming"

	@frappe.whitelist()
	def log_payment(
		self,
		payment_date=None,
		amount_paid=None,
		payment_mode="Bank Transfer / NEFT",
		reference_no=None,
		invoice_file=None,
		remarks=None,
	):
		"""
		Whitelisted API method to record a payment row and automatically advance the next renewal date.
		"""
		if not payment_date:
			payment_date = today()

		if not amount_paid or float(amount_paid) <= 0:
			frappe.throw(_("Amount Paid must be greater than zero."), frappe.ValidationError)

		amount_paid = float(amount_paid)

		# Append to child table
		self.append(
			"payment_history",
			{
				"payment_date": payment_date,
				"amount_paid": amount_paid,
				"currency": self.currency or "INR",
				"payment_mode": payment_mode,
				"reference_no": (reference_no or "").strip(),
				"invoice_file": invoice_file,
				"remarks": (remarks or "").strip(),
				"recorded_by": frappe.session.user,
				"recorded_on": now_datetime(),
			},
		)

		# Advance renewal date based on frequency
		p_date = getdate(payment_date)
		base_date = getdate(self.next_renewal_date) if self.next_renewal_date else p_date
		# If past due date, use payment date or due date whichever is later
		if base_date < p_date:
			base_date = p_date

		if self.renewal_frequency == "Annually":
			self.next_renewal_date = add_years(base_date, 1)
			self.renewal_status = "Upcoming"
		elif self.renewal_frequency == "Half-Yearly":
			self.next_renewal_date = add_months(base_date, 6)
			self.renewal_status = "Upcoming"
		elif self.renewal_frequency == "Quarterly":
			self.next_renewal_date = add_months(base_date, 3)
			self.renewal_status = "Upcoming"
		elif self.renewal_frequency == "Monthly":
			self.next_renewal_date = add_months(base_date, 1)
			self.renewal_status = "Upcoming"
		elif self.renewal_frequency == "One-off / Non-recurring":
			self.next_renewal_date = None
			self.renewal_status = "Completed / One-off"

		self.save()
		frappe.db.commit()

		return {
			"success": True,
			"next_renewal_date": str(self.next_renewal_date) if self.next_renewal_date else None,
			"renewal_status": self.renewal_status,
			"message": _("Payment logged successfully."),
		}

