# Copyright (c) 2026, Kishore and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, getdate, today

from tracora.api.assign import assign_asset, unassign_asset
from tracora.licences.roll_forward import advance_date_by_cycle, calculate_next_renewal
from tracora.licences.status import mark_expired_licences, recalculate_next_renewal_dates


class TestTracoraLicences(FrappeTestCase):
	def setUp(self):
		super().setUp()
		# Company
		if not frappe.db.exists("Tracora Company", "Licence Test Corp"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Licence Test Corp",
				"company_type": "Internal",
				"company_abbr": "LTC",
				"company_address": "789 Software Way, Chennai",
				"source": "Tracora"
			}).insert()

		# Branch
		if not frappe.db.exists("Tracora Branch", "Dev Branch - LTC"):
			frappe.get_doc({
				"doctype": "Tracora Branch",
				"branch_name": "Dev Branch",
				"company": "Licence Test Corp",
				"source": "Tracora"
			}).insert()

		# Department
		if not frappe.db.exists("Tracora Department", "Engineering - LTC"):
			frappe.get_doc({
				"doctype": "Tracora Department",
				"department_name": "Engineering",
				"company": "Licence Test Corp",
				"source": "Tracora"
			}).insert()

		# Location
		if not frappe.db.exists("Tracora Location", "Tech Park Floor 4"):
			frappe.get_doc({
				"doctype": "Tracora Location",
				"location_name": "Tech Park Floor 4",
				"address": "123 Tech Park Road",
				"latitude": 13.0827,
				"longitude": 80.2707
			}).insert()

	def _create_employee(self, code: str, name: str = "Test Dev") -> str:
		unique_code = f"{code}-{frappe.generate_hash(length=6)}"
		emp = frappe.get_doc({
			"doctype": "Tracora Employee",
			"employee_code": unique_code,
			"employee_name": name,
			"company": "Licence Test Corp",
			"branch": "Dev Branch - LTC",
			"department": "Engineering - LTC",
			"mobile": "9876543210",
			"status": "Active",
			"source": "Tracora"
		}).insert()
		return emp.name

	def _create_asset(self, serial: str) -> str:
		unique_serial = f"{serial}-{frappe.generate_hash(length=6)}"
		asset = frappe.get_doc({
			"doctype": "Tracora Asset",
			"asset_name": f"Laptop {unique_serial}",
			"brand": "Dell",
			"model": "Latitude 5420",
			"serial_no": unique_serial,
			"tag_mode": "Auto-generated",
			"category": "Laptop",
			"owner_company": "Licence Test Corp",
			"holding_company": "Licence Test Corp",
			"branch": "Dev Branch - LTC",
			"location": "Tech Park Floor 4",
			"condition": "Good",
			"status": "In Store"
		}).insert()
		return asset.name

	def test_fr20_licence_zero_seats_unassigned(self):
		"""FR-20, FR-86: A software licence with zero seats saves and reads Unassigned."""
		licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Figma Enterprise",
			"licence_name": "Figma Design Seats",
			"company": "Licence Test Corp",
			"licence_type": "User licence",
			"renewal_cycle": "Yearly",
			"licence_expiry_date": add_days(today(), 365),
			"seats": []
		}).insert()

		self.assertEqual(licence.licence_status, "Unassigned")

	def test_fr21_user_licence_requires_user_and_device(self):
		"""FR-21, FR-85: User licence requires both user and device; Device licence requires device only."""
		asset_name = self._create_asset("SN-LIC-01")

		# User licence missing user -> ValidationError
		with self.assertRaises(frappe.ValidationError) as ctx:
			frappe.get_doc({
				"doctype": "Tracora Software Licence",
				"software_name": "JetBrains All Products",
				"licence_name": "JetBrains Pack",
				"company": "Licence Test Corp",
				"licence_type": "User licence",
				"renewal_cycle": "Yearly",
				"licence_expiry_date": add_days(today(), 180),
				"seats": [
					{"device": asset_name, "user": None}
				]
			}).insert()
		self.assertIn("User is required", str(ctx.exception))

		# Device licence with device only -> succeeds
		dev_licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Windows 11 Pro OEM",
			"licence_name": "Win11 OEM",
			"company": "Licence Test Corp",
			"licence_type": "Device licence",
			"renewal_cycle": "One-time",
			"licence_expiry_date": add_days(today(), 1000),
			"seats": [
				{"device": asset_name, "user": None, "seat_status": "Active"}
			]
		}).insert()
		self.assertEqual(dev_licence.licence_status, "Active")

	def test_fr21_duplicate_user_device_pair_refused(self):
		"""FR-21: The same user and device cannot appear twice on one licence."""
		asset_name = self._create_asset("SN-LIC-02")
		emp_name = self._create_employee("EMP-LIC-02")

		with self.assertRaises(frappe.ValidationError) as ctx:
			frappe.get_doc({
				"doctype": "Tracora Software Licence",
				"software_name": "Postman Pro",
				"licence_name": "Postman API",
				"company": "Licence Test Corp",
				"licence_type": "User licence",
				"renewal_cycle": "Yearly",
				"licence_expiry_date": add_days(today(), 200),
				"seats": [
					{"device": asset_name, "user": emp_name, "seat_status": "Active"},
					{"device": asset_name, "user": emp_name, "seat_status": "Active"}
				]
			}).insert()
		self.assertIn("Duplicate user and device pair", str(ctx.exception))

	def test_fr23_renewal_calculation_quarterly_and_scheduler(self):
		"""FR-23: calculate_next_renewal advances quarterly cycle correctly to on or after reference date."""
		calc_date = calculate_next_renewal("2026-01-01", "Quarterly", reference_date="2026-03-01")
		self.assertEqual(str(calc_date), "2026-04-01")

		# One-time licences return None
		self.assertIsNone(calculate_next_renewal("2026-01-01", "One-time"))
		self.assertIsNone(calculate_next_renewal(None, "Monthly"))

		licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Zoom Rooms",
			"licence_name": "Zoom Conf",
			"company": "Licence Test Corp",
			"licence_type": "Device licence",
			"renewal_cycle": "Quarterly",
			"licence_start_date": "2026-01-01",
			"licence_expiry_date": add_days(today(), 365),
			"seats": []
		}).insert()

		self.assertIsNotNone(licence.next_renewal_date)
		self.assertGreaterEqual(getdate(licence.next_renewal_date), getdate(today()))

	def test_fr59_unassign_device_flags_seats_batch_safe(self):
		"""
		FR-59: Unassigning a device flags all active seats on that device without
		double-save race condition on parent licence.
		"""
		asset_name = self._create_asset("SN-LIC-03")
		emp_1 = self._create_employee("EMP-LIC-03A")
		emp_2 = self._create_employee("EMP-LIC-03B")

		# Assign asset to emp_1
		assign_asset(asset_name, emp_1, remarks="Assign laptop for software test")

		# Licence with 2 seats installed on this same device (User licence)
		licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "IntelliJ IDEA Ultimate",
			"licence_name": "IntelliJ Dev Pack",
			"company": "Licence Test Corp",
			"licence_type": "User licence",
			"renewal_cycle": "Yearly",
			"licence_expiry_date": add_days(today(), 300),
			"seats": [
				{"device": asset_name, "user": emp_1, "seat_status": "Active"},
				{"device": asset_name, "user": emp_2, "seat_status": "Active"}
			]
		}).insert()

		# Unassign the device
		unassign_asset(asset_name, location="Tech Park Floor 4", remarks="Returning laptop due to upgrade")

		# Both seats must be released
		licence.reload()
		for seat in licence.seats:
			self.assertEqual(seat.seat_status, "Released")

	def test_fr59_retire_device_flags_seats(self):
		"""FR-59: Retiring an asset releases active seats."""
		asset_name = self._create_asset("SN-LIC-04")
		emp = self._create_employee("EMP-LIC-04")

		licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Adobe CC",
			"licence_name": "Adobe Design",
			"company": "Licence Test Corp",
			"licence_type": "User licence",
			"renewal_cycle": "Yearly",
			"licence_expiry_date": add_days(today(), 120),
			"seats": [
				{"device": asset_name, "user": emp, "seat_status": "Active", "software_key": "KEY-ADOBE-1"}
			]
		}).insert()

		# Retire the asset
		asset_doc = frappe.get_doc("Tracora Asset", asset_name)
		asset_doc.status = "Retired"
		asset_doc.save()

		licence.reload()
		self.assertEqual(licence.seats[0].seat_status, "Released")

	def test_on_trash_blocks_asset_delete_with_attached_seats(self):
		"""Preserve link integrity: Deleting asset with attached seats is refused."""
		asset_name = self._create_asset("SN-LIC-05")
		emp = self._create_employee("EMP-LIC-05")

		frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Docker Desktop Business",
			"licence_name": "Docker Pro",
			"company": "Licence Test Corp",
			"licence_type": "User licence",
			"renewal_cycle": "Yearly",
			"licence_expiry_date": add_days(today(), 240),
			"seats": [
				{"device": asset_name, "user": emp, "seat_status": "Active", "software_key": "KEY-DOCKER"}
			]
		}).insert()

		asset_doc = frappe.get_doc("Tracora Asset", asset_name)
		with self.assertRaises(frappe.ValidationError) as ctx:
			asset_doc.delete()
		self.assertIn("software licence seats are still attached", str(ctx.exception))

	def test_fr60_exit_employee_blocked_by_active_or_flagged_seat(self):
		"""
		FR-60, FR-78: Exit is blocked by an active seat.
		Unblocked only when released.
		"""
		asset_name = self._create_asset("SN-LIC-06")
		emp_name = self._create_employee("EMP-LIC-06")

		licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Slack Enterprise",
			"licence_name": "Slack Seat",
			"company": "Licence Test Corp",
			"licence_type": "User licence",
			"renewal_cycle": "Yearly",
			"licence_expiry_date": add_days(today(), 300),
			"seats": [
				{"device": asset_name, "user": emp_name, "seat_status": "Active", "software_key": "KEY-SLACK"}
			]
		}).insert()

		emp_doc = frappe.get_doc("Tracora Employee", emp_name)

		# Attempt exit with Active seat -> blocked
		emp_doc.status = "Exited"
		with self.assertRaises(frappe.ValidationError) as ctx:
			emp_doc.save()
		self.assertIn("Software Licence Seats", str(ctx.exception))
		self.assertIn("Active: 1", str(ctx.exception))

		# Release seat -> exit succeeds
		licence.seats[0].seat_status = "Released"
		licence.save()

		emp_doc.reload()
		emp_doc.status = "Exited"
		emp_doc.save()
		self.assertEqual(emp_doc.status, "Exited")

	def test_fr69_pending_clearance_blocked_by_active_seat(self):
		"""
		FR-69: Pending Clearance employee unassigning asset with remaining active seats
		remains Pending Clearance until all assets and seats are cleared.
		"""
		asset_1 = self._create_asset("SN-LIC-07A")
		asset_2 = self._create_asset("SN-LIC-07B")
		emp_name = self._create_employee("EMP-LIC-07")

		assign_asset(asset_1, emp_name, remarks="Assign asset 1 before clearance")
		assign_asset(asset_2, emp_name, remarks="Assign asset 2 before clearance")

		frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Tableau Creator",
			"licence_name": "Tableau Seat",
			"company": "Licence Test Corp",
			"licence_type": "User licence",
			"renewal_cycle": "Yearly",
			"licence_expiry_date": add_days(today(), 250),
			"seats": [
				{"device": asset_2, "user": emp_name, "seat_status": "Active", "software_key": "KEY-TAB"}
			]
		}).insert()

		# Put employee into Pending Clearance
		frappe.db.set_value("Tracora Employee", emp_name, "status", "Pending Clearance")

		# Unassign only asset 1
		unassign_asset(asset_1, location="Tech Park Floor 4", remarks="Clearance handover asset 1")

		# Employee still holds asset 2 with its active seat -> remains Pending Clearance
		emp_status = frappe.db.get_value("Tracora Employee", emp_name, "status")
		self.assertEqual(emp_status, "Pending Clearance")

		# Unassign asset 2 (releases active seat automatically)
		unassign_asset(asset_2, location="Tech Park Floor 4", remarks="Clearance handover asset 2")

		# Fully cleared -> auto-transitions to Exited
		emp_status = frappe.db.get_value("Tracora Employee", emp_name, "status")
		self.assertEqual(emp_status, "Exited")

	def test_mark_expired_licences_job(self):
		"""Daily job updates expired licences."""
		licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Expired SaaS Tool",
			"licence_name": "Expired Tool Licence",
			"company": "Licence Test Corp",
			"licence_type": "Device licence",
			"renewal_cycle": "Monthly",
			"licence_expiry_date": "2025-01-01",
			"seats": []
		}).insert()

		frappe.db.set_value("Tracora Software Licence", licence.name, "licence_status", "Active")

		count = mark_expired_licences()
		self.assertGreaterEqual(count, 1)

		licence.reload()
		self.assertEqual(licence.licence_status, "Expired")

	def test_zero_seat_past_expiry_licence_remains_unassigned(self):
		"""FR-20 / P8 audit regression: Confirm a licence with 0 seats and a past expiry
		date shows 'Unassigned' on save and continues to show 'Unassigned' after the
		daily scheduler job mark_expired_licences runs."""
		licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Zero Seat Expired Pool",
			"licence_name": "Unassigned Pool Pack",
			"company": "Licence Test Corp",
			"licence_type": "Device licence",
			"renewal_cycle": "Monthly",
			"licence_expiry_date": add_days(today(), -20),
			"seats": []
		}).insert()

		self.assertEqual(licence.licence_status, "Unassigned")

		mark_expired_licences()

		licence.reload()
		self.assertEqual(licence.licence_status, "Unassigned")

	def test_roll_forward_unassigned_licence_allowed(self):
		"""Confirm a 0-seat licence with a set start date correctly gets next_renewal_date
		calculated and preserves 'Unassigned' status."""
		past_start = add_months(today(), -2)
		licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Unallocated Tool",
			"licence_name": "Pool Pack",
			"company": "Licence Test Corp",
			"licence_type": "User licence",
			"renewal_cycle": "Monthly",
			"licence_start_date": past_start,
			"licence_expiry_date": add_months(today(), 1),
			"seats": []
		}).insert()
		self.assertEqual(licence.licence_status, "Unassigned")
		self.assertIsNotNone(licence.next_renewal_date)
		self.assertGreaterEqual(getdate(licence.next_renewal_date), getdate(today()))

	def test_roll_forward_restores_expired_unassigned_licence(self):
		"""Test daily scheduler recalculate_next_renewal_dates advances next_renewal_date
		and updates last_renewed_on when a renewal checkpoint is crossed."""
		past_start = add_months(today(), -3)
		licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Lapsed Pool Tool",
			"licence_name": "Lapsed Pack",
			"company": "Licence Test Corp",
			"licence_type": "User licence",
			"renewal_cycle": "Monthly",
			"licence_start_date": past_start,
			"licence_expiry_date": add_days(today(), 30),
			"seats": []
		}).insert()

		# Backdate stored next_renewal_date to simulate reaching a renewal checkpoint
		old_next = add_months(today(), -1)
		frappe.db.set_value("Tracora Software Licence", licence.name, "next_renewal_date", old_next)
		licence.reload()
		self.assertEqual(getdate(licence.next_renewal_date), getdate(old_next))

		recalculate_next_renewal_dates()
		licence.reload()

		self.assertGreater(getdate(licence.next_renewal_date), getdate(old_next))
		self.assertGreaterEqual(getdate(licence.next_renewal_date), getdate(today()))
		self.assertEqual(getdate(licence.last_renewed_on), getdate(today()))
		self.assertEqual(licence.licence_status, "Unassigned")

	def test_get_installed_licences_authorization(self):
		"""
		Seats API authorization:
		(a) An authorized user with read access on Asset and Software Licence gets correct seat data.
		(b) A user without read access on Tracora Software Licence is refused with PermissionError.
		"""
		from tracora.licences.seats import get_installed_licences

		asset_name = self._create_asset("SN-LIC-SEAT-AUTH")
		emp_name = self._create_employee("EMP-LIC-SEAT-AUTH")

		licence = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Secured Dev Tool",
			"licence_name": "Secured Pack",
			"company": "Licence Test Corp",
			"licence_type": "User licence",
			"renewal_cycle": "Monthly",
			"licence_expiry_date": add_days(today(), 60),
			"seats": [
				{"device": asset_name, "user": emp_name, "seat_status": "Active"}
			]
		}).insert()

		admin_user = "test_tracora_admin@example.com"
		if not frappe.db.exists("User", admin_user):
			u = frappe.get_doc({
				"doctype": "User",
				"email": admin_user,
				"first_name": "Test",
				"last_name": "Admin",
				"roles": [{"role": "Tracora Admin"}]
			})
			u.flags.no_welcome_mail = True
			u.insert(ignore_permissions=True)

		unprivileged_user = "test_unprivileged_seat_reader@example.com"
		if not frappe.db.exists("User", unprivileged_user):
			u2 = frappe.get_doc({
				"doctype": "User",
				"email": unprivileged_user,
				"first_name": "Unprivileged",
				"last_name": "Reader",
				"roles": [{"role": "Desk User"}]
			})
			u2.flags.no_welcome_mail = True
			u2.insert(ignore_permissions=True)

		# (a) Authorized user receives correct seat data
		frappe.set_user(admin_user)
		seats = get_installed_licences(asset_name)
		self.assertEqual(len(seats), 1)
		self.assertEqual(seats[0]["parent"], licence.name)
		self.assertEqual(seats[0]["device"], asset_name)
		self.assertEqual(seats[0]["seat_status"], "Active")

		# (b) User without read access on Tracora Software Licence is refused with PermissionError
		frappe.set_user(unprivileged_user)
		with self.assertRaises(frappe.PermissionError):
			get_installed_licences(asset_name)

		# Reset session to Administrator
		frappe.set_user("Administrator")

	def test_seat_capacity_and_depleted_status(self):
		"""Test seat range capacity enforcement and real-time Available/Depleted status."""
		dev1 = self._create_asset("SN-CAP-001")
		dev2 = self._create_asset("SN-CAP-002")
		dev3 = self._create_asset("SN-CAP-003")
		emp1 = self._create_employee("EMP-CAP-001")
		emp2 = self._create_employee("EMP-CAP-002")
		emp3 = self._create_employee("EMP-CAP-003")

		# 1. Negative total_seats is rejected
		with self.assertRaises(frappe.ValidationError) as cm:
			frappe.get_doc({
				"doctype": "Tracora Software Licence",
				"software_name": "Capacity Test App",
				"licence_name": "Cap Test Invalid",
				"company": "Licence Test Corp",
				"licence_type": "User licence",
				"renewal_cycle": "Monthly",
				"licence_expiry_date": add_days(today(), 60),
				"total_seats": 0
			}).insert()
		self.assertIn("Total Seats must be at least 1", str(cm.exception))

		# 2. Create licence with total_seats = 2
		lic = frappe.get_doc({
			"doctype": "Tracora Software Licence",
			"software_name": "Capacity Test App",
			"licence_name": "Cap Test 2 Seats",
			"company": "Licence Test Corp",
			"licence_type": "User licence",
			"renewal_cycle": "Monthly",
			"licence_expiry_date": add_days(today(), 60),
			"total_seats": 2,
			"seats": [
				{"device": dev1, "user": emp1, "seat_status": "Active"}
			]
		}).insert()

		self.assertEqual(lic.total_seats, 2)
		self.assertEqual(lic.allocated_seats, 1)
		self.assertEqual(lic.seat_availability, "Available")

		# 3. Add second seat -> capacity reached, status becomes Depleted
		lic.append("seats", {"device": dev2, "user": emp2, "seat_status": "Active"})
		lic.save()
		self.assertEqual(lic.allocated_seats, 2)
		self.assertEqual(lic.seat_availability, "Depleted")

		# 4. Attempt to add third active seat -> hard blocked by validation error
		lic.append("seats", {"device": dev3, "user": emp3, "seat_status": "Active"})
		with self.assertRaises(frappe.ValidationError) as cm:
			lic.save()
		self.assertIn("capacity is depleted", str(cm.exception))

		# 5. Reload fresh doc from DB, release seat 2 -> status returns to Available
		lic.reload()
		lic.seats[1].seat_status = "Released"
		lic.save()
		self.assertEqual(lic.allocated_seats, 1)
		self.assertEqual(lic.seat_availability, "Available")

