# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class TracoraEmployee(Document):
	def autoname(self):
		company_type = frappe.db.get_value("Tracora Company", self.company, "company_type") if self.company else None
		if company_type == "External":
			series_name = make_autoname("EXT-.######")
			self.name = series_name
			self.employee_code = series_name
		else:
			if not self.employee_code or not str(self.employee_code).strip():
				frappe.throw(_("Employee Code is required for internal company personnel."), frappe.ValidationError)
			code = str(self.employee_code).strip()
			if frappe.db.exists("Tracora Employee", code):
				frappe.throw(_("Employee Code '{0}' already exists.").format(code), frappe.DuplicateEntryError)
			self.name = code
			self.employee_code = code

	def validate(self):
		company_type = frappe.db.get_value("Tracora Company", self.company, "company_type") if self.company else None
		if company_type == "External":
			personal_violations = []
			if self.date_of_birth:
				personal_violations.append("Date of Birth")
			if self.aadhaar_number:
				personal_violations.append("Aadhaar Number")
			if self.permanent_address:
				personal_violations.append("Permanent Address")
			if personal_violations:
				frappe.throw(
					_("Personal details ({0}) cannot be stored for External company personnel ({1}) (FR-75, Rule 9).").format(
						", ".join(personal_violations), self.company
					),
					frappe.ValidationError
				)
		elif company_type == "Internal" and self.source == "Tracora":
			if not self.branch or not self.department:
				frappe.throw(
					_("Branch and Department are required on manual entry for internal company employees ({0}) (FR-72).").format(
						self.company
					),
					frappe.ValidationError
				)

		if self.aadhaar_number:
			clean_aadhaar = str(self.aadhaar_number).replace(" ", "").replace("-", "")
			if not (len(clean_aadhaar) == 12 and clean_aadhaar.isdigit()):
				frappe.throw(_("Aadhaar Number must be a valid 12-digit number."), frappe.ValidationError)
			self.aadhaar_number = clean_aadhaar

		# FR-78, FR-10, FR-60: An employee cannot be marked exited or inactive while holding any asset or licence seat
		if self.status in ("Exited", "Inactive"):
			held_assets = frappe.db.get_all(
				"Tracora Asset",
				filters={"assigned_to": self.name},
				fields=["name", "asset_tag", "asset_name"]
			)
			held_seats = []
			if frappe.db.exists("DocType", "Tracora Licence Seat"):
				held_seats = frappe.db.get_all(
					"Tracora Licence Seat",
					filters={"user": self.name, "seat_status": ["in", ["Active", "Flagged"]]},
					fields=["name", "parent", "device", "seat_status"]
				)

			if held_assets or held_seats:
				violations = []
				if held_assets:
					held_str = ", ".join([f"{a.asset_tag or a.name} ({a.asset_name})" for a in held_assets])
					violations.append(_("Assets: {0}").format(held_str))
				if held_seats:
					active_s = [s for s in held_seats if s.seat_status == "Active"]
					flagged_s = [s for s in held_seats if s.seat_status == "Flagged"]
					seat_str = ", ".join([f"{s.parent} (Seat #{s.name}, Device {s.device}, {s.seat_status})" for s in held_seats])
					violations.append(_("Software Licence Seats: {0} (Active: {1}, Flagged: {2})").format(seat_str, len(active_s), len(flagged_s)))

				frappe.throw(
					_("Cannot mark employee '{0}' as {1} while they hold outstanding items: {2} (FR-78, FR-10, FR-60). Clear or release all items before exit.").format(
						self.name, self.status, "; ".join(violations)
					),
					frappe.ValidationError
				)

	def on_trash(self):
		# FR-87: An employee who appears anywhere in movement history cannot be deleted
		movements = frappe.db.get_all(
			"Tracora Asset Movement",
			filters={"from_employee": self.name},
			fields=["name", "movement_type"],
			limit=1
		) or frappe.db.get_all(
			"Tracora Asset Movement",
			filters={"to_employee": self.name},
			fields=["name", "movement_type"],
			limit=1
		)
		if movements:
			frappe.throw(
				_("Cannot delete employee '{0}' because they appear in asset movement history ({1}: {2}) (FR-87).").format(
					self.name, movements[0].name, movements[0].movement_type
				),
				frappe.ValidationError
			)
