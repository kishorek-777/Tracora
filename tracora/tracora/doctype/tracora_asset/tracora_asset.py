# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class TracoraAsset(Document):
	def autoname(self):
		if self.tag_mode == "Auto-generated":
			prefix = frappe.db.get_single_value("Tracora Settings", "tag_prefix") or "TRC-"
			if not prefix.endswith("-") and not prefix.endswith("."):
				prefix = f"{prefix}-"
			self.asset_tag = make_autoname(f"{prefix}.######")
		elif self.tag_mode == "Manual entry":
			if not self.asset_tag or not str(self.asset_tag).strip():
				frappe.throw(
					_("Asset Tag is required when Tag Mode is 'Manual entry'."),
					frappe.ValidationError
				)
			self.asset_tag = str(self.asset_tag).strip()
		else:
			frappe.throw(
				_("Please select a Tag Mode ('Auto-generated' or 'Manual entry') (FR-41)."),
				frappe.ValidationError
			)
		self.name = self.asset_tag

	def validate(self):
		# FR-66, FR-67: Reserved prefix check for manual tags
		if self.tag_mode == "Manual entry" and self.asset_tag:
			prefix = (frappe.db.get_single_value("Tracora Settings", "tag_prefix") or "TRC-").strip().upper()
			clean_prefix = prefix.rstrip("-").rstrip(".")
			tag_upper = self.asset_tag.strip().upper()
			if tag_upper.startswith(clean_prefix):
				frappe.throw(
					_("Manual asset tag '{0}' cannot start with reserved prefix '{1}' (FR-66, FR-67).").format(
						self.asset_tag, prefix
					),
					frappe.ValidationError
				)

		# Rule 8, FR-13: Cross-field namespace uniqueness
		# 1. Candidate tag uniqueness against other asset tags
		tag_in_tags = frappe.db.get_value(
			"Tracora Asset",
			{"asset_tag": self.asset_tag, "name": ["!=", self.name]},
			["name", "asset_name"],
			as_dict=True
		)
		if tag_in_tags:
			frappe.throw(
				_("Asset tag '{0}' is already used by asset '{1}' ({2}).").format(
					self.asset_tag, tag_in_tags.name, tag_in_tags.asset_name
				),
				frappe.DuplicateEntryError
			)

		# 2. Candidate tag uniqueness against ANY asset serial number
		tag_in_serials = frappe.db.get_value(
			"Tracora Asset",
			{"serial_no": self.asset_tag, "name": ["!=", self.name]},
			["name", "asset_name"],
			as_dict=True
		)
		if tag_in_serials:
			frappe.throw(
				_("Asset tag '{0}' matches the serial number of asset '{1}' ({2}). Tag and serial share one namespace (FR-13, Rule 8).").format(
					self.asset_tag, tag_in_serials.name, tag_in_serials.asset_name
				),
				frappe.ValidationError
			)

		# 3. Candidate serial uniqueness against ANY asset tag
		serial_in_tags = frappe.db.get_value(
			"Tracora Asset",
			{"asset_tag": self.serial_no, "name": ["!=", self.name]},
			["name", "asset_name"],
			as_dict=True
		)
		if serial_in_tags:
			frappe.throw(
				_("Serial number '{0}' matches the asset tag of asset '{1}' ({2}). Tag and serial share one namespace (FR-13, Rule 8).").format(
					self.serial_no, serial_in_tags.name, serial_in_tags.asset_name
				),
				frappe.ValidationError
			)

		# 4. Candidate serial uniqueness per brand (dynamically evaluates current brand on save)
		serial_in_brand = frappe.db.get_value(
			"Tracora Asset",
			{"serial_no": self.serial_no, "brand": self.brand, "name": ["!=", self.name]},
			["name", "asset_name", "brand"],
			as_dict=True
		)
		if serial_in_brand:
			frappe.throw(
				_("Serial number '{0}' already exists for brand '{1}' on asset '{2}' ({3}) (FR-13).").format(
					self.serial_no, self.brand, serial_in_brand.name, serial_in_brand.asset_name
				),
				frappe.DuplicateEntryError
			)

		# FR-05: Mandatory location
		if not self.location:
			frappe.throw(
				_("Location is required for an asset (FR-05)."),
				frappe.ValidationError
			)

		# FR-12, FR-72: Conditional branch requirement for Internal holding company
		if self.holding_company:
			company_type = frappe.db.get_value("Tracora Company", self.holding_company, "company_type")
			if company_type == "Internal" and not self.branch:
				frappe.throw(
					_("Branch is required when holding company '{0}' is Internal (FR-12, FR-72).").format(
						self.holding_company
					),
					frappe.ValidationError
				)

		# FR-93: Shared equipment rules
		if self.is_shared:
			if self.assigned_to:
				frappe.throw(
					_("Asset '{0}' is marked as shared equipment and cannot be assigned to an individual ({1}) (FR-93).").format(
						self.asset_tag or self.name, self.assigned_to
					),
					frappe.ValidationError
				)

		if self.point_of_contact:
			poc_status = frappe.db.get_value("Tracora Employee", self.point_of_contact, "status")
			if poc_status == "Exited":
				frappe.throw(
					_("Point of contact '{0}' has status 'Exited'. Please select an active employee (FR-93).").format(
						self.point_of_contact
					),
					frappe.ValidationError
				)

		# Rule 1, FR-82: Protection of custody and ownership fields against direct form editing
		if not self.is_new():
			before_doc = self.get_doc_before_save()
			if before_doc:
				if before_doc.assigned_to != self.assigned_to and not getattr(frappe.flags, "in_tracora_assign", False):
					frappe.throw(
						_("Assigned To cannot be edited directly. Use the Assign/Unassign action (Rule 1)."),
						frappe.ValidationError
					)
				if before_doc.assigned_on != self.assigned_on and not getattr(frappe.flags, "in_tracora_assign", False):
					frappe.throw(
						_("Assigned On cannot be edited directly. Use the Assign/Unassign action (Rule 1)."),
						frappe.ValidationError
					)
				if before_doc.owner_company != self.owner_company and not getattr(frappe.flags, "in_tracora_transfer", False):
					frappe.throw(
						_("Owner Company cannot be changed by editing. Use the Transfer Ownership action (FR-82, Rule 1)."),
						frappe.ValidationError
					)
		# FR-59: Flag active seats when asset is retired
		if not self.is_new():
			before_doc = self.get_doc_before_save()
			if before_doc and before_doc.status != "Retired" and self.status == "Retired":
				from tracora.licences.flagging import flag_active_seats_for_device
				flag_active_seats_for_device(self.name, _("Device '{0}' was retired").format(self.asset_tag or self.name))

	def on_trash(self):
		# Deliberate deviation from FR-59: deletion is blocked, not flagged, to preserve reqd FK integrity on Tracora Licence Seat.device
		if frappe.db.exists("DocType", "Tracora Licence Seat"):
			linked_seats = frappe.db.get_all(
				"Tracora Licence Seat",
				filters={"device": self.name, "seat_status": ["in", ["Active", "Flagged"]]},
				fields=["name", "parent", "seat_status"]
			)
			if linked_seats:
				seat_info = ", ".join([f"{s.parent} (Seat #{s.name}, {s.seat_status})" for s in linked_seats])
				frappe.throw(
					_("Cannot delete asset '{0}' because software licence seats are still attached: {1}. Release or reassign the seats first.").format(
						self.asset_tag or self.name, seat_info
					),
					frappe.ValidationError
				)
