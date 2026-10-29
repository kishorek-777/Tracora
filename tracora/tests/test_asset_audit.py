# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today
from tracora.api.audit import get_asset_audit_history, submit_asset_audit
from tracora.api.lookup import find_asset


class TestAssetAudit(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.created_users = []
		cls.created_docs = []

		cls.auditor_user = cls.create_test_user("test_auditor_pwa@example.com", ["Tracora Auditor"])
		cls.admin_user = cls.create_test_user("test_admin_audit@example.com", ["Tracora Admin"])
		cls.plain_user = cls.create_test_user("test_plain_audit@example.com", ["HR User"])

		frappe.set_user("Administrator")
		if not frappe.db.exists("Tracora Company", "Test Label Corp"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Test Label Corp",
				"company_type": "Internal",
				"company_abbr": "TLC",
				"company_address": "100 Label St, Chennai",
				"source": "Tracora",
			}).insert()

		if not frappe.db.exists("Tracora Branch", "HQ - TLC"):
			frappe.get_doc({
				"doctype": "Tracora Branch",
				"branch_name": "HQ",
				"company": "Test Label Corp",
				"source": "Tracora",
			}).insert()

		if not frappe.db.exists("Tracora Location", "HQ Main Store"):
			frappe.get_doc({
				"doctype": "Tracora Location",
				"location_name": "HQ Main Store",
				"address": "Floor 1, HQ Building, Chennai",
				"latitude": 13.0827,
				"longitude": 80.2707,
				"source": "Tracora",
			}).insert()

		cls.test_asset = frappe.get_doc({
			"doctype": "Tracora Asset",
			"tag_mode": "Auto-generated",
			"asset_name": "Audit Test Laptop ThinkPad",
			"brand": "Lenovo",
			"serial_no": f"SN-AUD-{frappe.generate_hash(length=8).upper()}",
			"owner_company": "Test Label Corp",
			"holding_company": "Test Label Corp",
			"branch": "HQ - TLC",
			"location": "HQ Main Store",
			"status": "In Store",
			"condition": "Good",
		}).insert(ignore_permissions=True)
		cls.created_docs.append(cls.test_asset)

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		if hasattr(cls, "test_asset") and cls.test_asset:
			frappe.db.sql("DELETE FROM `tabTracora Asset Audit Log` WHERE asset = %s", (cls.test_asset.name,))
			frappe.db.commit()

		for doc in reversed(cls.created_docs):
			if frappe.db.exists(doc.doctype, doc.name):
				frappe.delete_doc(doc.doctype, doc.name, force=True, ignore_permissions=True)
		for email in cls.created_users:
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDownClass()

	@classmethod
	def create_test_user(cls, email, roles):
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)

		user = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
			"roles": [{"role": r} for r in roles],
		}).insert(ignore_permissions=True)
		cls.created_users.append(email)
		return email

	def test_01_auditor_can_submit_audit(self):
		"""Tracora Auditor can submit audit log, which updates Tracora Asset summary fields."""
		frappe.set_user(self.auditor_user)

		res = submit_asset_audit(
			asset=self.test_asset.name,
			audit_status="Verified",
			remarks="Physical tag and serial verified intact.",
			condition="Good",
		)
		self.assertTrue(res.get("success"))
		self.assertEqual(res.get("audit_status"), "Verified")
		log_name = res.get("audit_log")

		# Check DB record
		audit_doc = frappe.get_doc("Tracora Asset Audit Log", log_name)
		self.assertEqual(audit_doc.asset, self.test_asset.name)
		self.assertEqual(audit_doc.auditor, self.auditor_user)
		self.assertEqual(audit_doc.audit_status, "Verified")
		self.assertEqual(str(audit_doc.audit_date), today())

		# Check summary fields on Tracora Asset
		asset_doc = frappe.get_doc("Tracora Asset", self.test_asset.name)
		self.assertEqual(str(asset_doc.audit_date), today())
		self.assertIn("[Verified]", asset_doc.audit_remarks)
		self.assertIn("verified intact", asset_doc.audit_remarks)

	def test_02_audit_log_immutable(self):
		"""Audit log entries cannot be modified once inserted (RBAC and DocType validator)."""
		frappe.set_user(self.auditor_user)
		res = submit_asset_audit(
			asset=self.test_asset.name,
			audit_status="Verified",
			remarks="Initial audit remark.",
		)
		log_name = res["audit_log"]

		log_doc = frappe.get_doc("Tracora Asset Audit Log", log_name)
		log_doc.remarks = "Attempted tampered remark"

		# Auditor has no write permission
		with self.assertRaises(frappe.PermissionError):
			log_doc.save()

		# Even bypassing permissions, document-level validator forbids modification
		with self.assertRaises(frappe.ValidationError):
			log_doc.save(ignore_permissions=True)

	def test_03_audit_log_cannot_be_deleted(self):
		"""Audit log entries cannot be deleted (append-only ledger)."""
		frappe.set_user("Administrator")
		log_doc = frappe.get_doc({
			"doctype": "Tracora Asset Audit Log",
			"asset": self.test_asset.name,
			"audit_date": today(),
			"auditor": self.auditor_user,
			"audit_status": "Verified",
			"remarks": "Log for deletion test",
		}).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			log_doc.delete()

	def test_04_unauthorized_user_blocked(self):
		"""Non-Tracora user cannot submit audit or retrieve audit history."""
		frappe.set_user(self.plain_user)
		with self.assertRaises(frappe.PermissionError):
			submit_asset_audit(
				asset=self.test_asset.name,
				audit_status="Verified",
				remarks="Unauthorized attempt",
			)

		with self.assertRaises(frappe.PermissionError):
			get_asset_audit_history(asset=self.test_asset.name)

	def test_05_auditor_can_lookup_asset_and_see_audit_history(self):
		"""Auditor can look up asset via find_asset and receive audit history."""
		frappe.set_user(self.auditor_user)
		payload = find_asset(q=self.test_asset.asset_tag)
		self.assertEqual(payload.get("match_type"), "single")
		self.assertEqual(payload["asset"]["name"], self.test_asset.name)
		self.assertIn("audit_history", payload)
		self.assertGreaterEqual(len(payload["audit_history"]), 1)
		self.assertEqual(payload["audit_history"][0]["audit_status"], "Verified")
		self.assertEqual(payload["audit_history"][0]["auditor"], self.auditor_user)

	def test_06_validation_rules(self):
		"""Validation rules: non-existent asset, empty remarks, future date, invalid status."""
		frappe.set_user(self.auditor_user)

		# Non-existent asset
		with self.assertRaises(frappe.DoesNotExistError):
			submit_asset_audit(asset="TRC-NON-EXISTENT", remarks="test")

		# Empty remarks
		with self.assertRaises(frappe.ValidationError):
			submit_asset_audit(asset=self.test_asset.name, remarks="   ")

		# Invalid status
		with self.assertRaises(frappe.ValidationError):
			submit_asset_audit(asset=self.test_asset.name, audit_status="InvalidStatus", remarks="test")

		# Future date on doc
		future_doc = frappe.get_doc({
			"doctype": "Tracora Asset Audit Log",
			"asset": self.test_asset.name,
			"audit_date": add_days(today(), 5),
			"auditor": self.auditor_user,
			"remarks": "Future test",
		})
		with self.assertRaises(frappe.ValidationError):
			future_doc.insert()
