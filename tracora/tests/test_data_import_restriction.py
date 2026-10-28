# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.core.doctype.data_import.data_import import get_import_logs
from tracora.patches.v1_0.restrict_data_import_and_perms import execute as run_patch
from tracora.permissions import (
	has_data_import_permission,
	get_data_import_query_conditions,
	validate_data_import,
	is_restricted_user,
)


class TestDataImportRestriction(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.created_users = []
		cls.created_docs = []

		# Ensure patch has been executed
		run_patch()

		cls.admin_user = cls.create_test_user("test_tracora_admin_di@example.com", ["Tracora Admin"])
		cls.super_admin_user = cls.create_test_user("test_tracora_super_di@example.com", ["Tracora Super Admin"])
		cls.sys_mgr_user = cls.create_test_user("test_sys_mgr_di@example.com", ["System Manager"])
		cls.both_user = cls.create_test_user("test_both_admin_sys_di@example.com", ["Tracora Admin", "System Manager"])

		# Non-tracora role: HR User or similar
		non_tracora_role = "HR User" if frappe.db.exists("Role", "HR User") else "Blogger"
		cls.plain_user = cls.create_test_user("test_plain_di@example.com", [non_tracora_role])

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for doc in cls.created_docs:
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
			"enabled": 1,
			"send_welcome_email": 0,
			"roles": [{"role": r} for r in roles],
		}).insert(ignore_permissions=True)
		cls.created_users.append(email)
		return email

	def test_01_tracora_admin_can_create_import_for_allowed_doctypes(self):
		"""Restricted user with only Tracora Admin can create a Data Import for Tracora Asset and Tracora Software Licence."""
		frappe.set_user(self.admin_user)

		for dt in ["Tracora Asset", "Tracora Software Licence"]:
			di = frappe.get_doc({
				"doctype": "Data Import",
				"reference_doctype": dt,
				"import_type": "Insert New Records",
			}).insert()
			self.created_docs.append(di)
			self.assertTrue(di.name)
			self.assertEqual(di.reference_doctype, dt)

	def test_02_tracora_admin_blocked_for_disallowed_doctypes(self):
		"""Same user is blocked for Tracora Employee, User, File, ToDo and Customer, at validate and has_permission."""
		frappe.set_user(self.admin_user)

		blocked_doctypes = ["Tracora Employee", "User", "File", "ToDo", "Customer"]
		for dt in blocked_doctypes:
			# Blocked at validate/insert: raises PermissionError or ValidationError
			with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
				di = frappe.get_doc({
					"doctype": "Data Import",
					"reference_doctype": dt,
					"import_type": "Insert New Records",
				})
				di.insert()

			# Blocked at has_permission for non-Tracora doctypes
			if dt != "Tracora Employee":
				doc = frappe.new_doc("Data Import")
				doc.reference_doctype = dt
				has_perm = frappe.has_permission("Data Import", "read", doc=doc, user=self.admin_user)
				self.assertFalse(has_perm, f"has_permission must be False for {dt}")

	def test_03_restricted_user_cannot_read_non_tracora_import_and_list_filtered(self):
		"""Same user cannot read a Data Import whose reference_doctype is non-Tracora, and frappe.get_list on Data Import returns only Tracora ones."""
		frappe.set_user("Administrator")
		admin_di = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "Event",
			"import_type": "Insert New Records",
		}).insert()
		self.created_docs.append(admin_di)

		tracora_di = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "Tracora Asset",
			"import_type": "Insert New Records",
		}).insert()
		self.created_docs.append(tracora_di)

		frappe.set_user(self.admin_user)
		# Direct read check on non-Tracora import raises PermissionError
		with self.assertRaises(frappe.PermissionError):
			doc = frappe.get_doc("Data Import", admin_di.name)
			doc.check_permission("read")

		# get_list only returns Tracora imports
		import_list = frappe.get_list("Data Import", fields=["name", "reference_doctype"])
		import_names = [d.name for d in import_list]
		self.assertNotIn(admin_di.name, import_names)
		self.assertIn(tracora_di.name, import_names)

		# Ensure all returned reference_doctypes belong to Tracora module
		for item in import_list:
			mod = frappe.db.get_value("DocType", item.reference_doctype, "module")
			self.assertEqual(mod, "Tracora")

	def test_04_super_admin_behaves_same_and_has_no_delete(self):
		"""Tracora Super Admin behaves the same and has no delete on Data Import."""
		frappe.set_user(self.super_admin_user)

		# Allowed create
		di = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "Tracora Asset",
			"import_type": "Insert New Records",
		}).insert()
		self.created_docs.append(di)

		# Disallowed create
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc({
				"doctype": "Data Import",
				"reference_doctype": "Event",
				"import_type": "Insert New Records",
			}).insert()

		# No delete permission on Data Import
		has_delete = frappe.has_permission("Data Import", "delete", doc=di, user=self.super_admin_user)
		self.assertFalse(has_delete, "Tracora Super Admin must not have delete permission on Data Import")
		with self.assertRaises(frappe.PermissionError):
			di.delete()

	def test_05_admin_plus_system_manager_unaffected(self):
		"""A user with Tracora Admin AND System Manager is unaffected and sees all Data Imports."""
		frappe.set_user(self.both_user)

		# Can create non-Tracora import
		di = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "Event",
			"import_type": "Insert New Records",
		}).insert()
		self.created_docs.append(di)

		# Can read all imports in list
		items = frappe.get_list("Data Import", pluck="name")
		self.assertIn(di.name, items)

	def test_06_administrator_and_system_manager_unaffected(self):
		"""Administrator and a System Manager only user are unaffected, and System Manager keeps identical access."""
		for user in ["Administrator", self.sys_mgr_user]:
			frappe.set_user(user)
			di = frappe.get_doc({
				"doctype": "Data Import",
				"reference_doctype": "Event",
				"import_type": "Insert New Records",
			}).insert()
			self.created_docs.append(di)
			self.assertTrue(frappe.has_permission("Data Import", "read", doc=di, user=user))
			self.assertTrue(frappe.has_permission("Data Import", "write", doc=di, user=user))
			self.assertTrue(frappe.has_permission("Data Import", "create", doc=di, user=user))
			self.assertTrue(frappe.has_permission("Data Import", "delete", doc=di, user=user))

	def test_07_non_tracora_user_unchanged(self):
		"""A user with no Tracora role (and no System Manager) cannot access Data Import."""
		frappe.set_user(self.plain_user)
		has_read = frappe.has_permission("Data Import", "read", user=self.plain_user)
		self.assertFalse(has_read)

	def test_08_get_import_logs_behavior(self):
		"""get_import_logs works for restricted user on Tracora import and is refused on non-Tracora import."""
		frappe.set_user("Administrator")
		tracora_di = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "Tracora Asset",
			"import_type": "Insert New Records",
		}).insert()
		self.created_docs.append(tracora_di)

		non_tracora_di = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "Event",
			"import_type": "Insert New Records",
		}).insert()
		self.created_docs.append(non_tracora_di)

		frappe.set_user(self.admin_user)
		# Allowed for Tracora import
		logs = get_import_logs(tracora_di.name)
		self.assertIsInstance(logs, list)

		# Refused for non-Tracora import
		with self.assertRaises(frappe.PermissionError):
			get_import_logs(non_tracora_di.name)

	def test_09_direct_get_list_data_import_log_refused(self):
		"""Direct get_list on Data Import Log is still refused for restricted user."""
		frappe.set_user(self.admin_user)
		# Tracora Admin does not have read on Data Import Log doctype
		has_read = frappe.has_permission("Data Import Log", "read", user=self.admin_user)
		self.assertFalse(has_read, "Restricted user must not have read permission on Data Import Log doctype")

	def test_10_target_doctype_allow_import_and_docperm(self):
		"""Tracora Employee has allow_import 0 and the 6 doctypes have no import flag for Admin or Super Admin."""
		frappe.set_user("Administrator")
		disallowed = [
			"Tracora Employee",
			"Tracora Company",
			"Tracora Branch",
			"Tracora Department",
			"Tracora Location",
			"Tracora Maintenance Log",
		]
		for dt in disallowed:
			allow_import = frappe.db.get_value("DocType", dt, "allow_import")
			self.assertEqual(allow_import, 0, f"{dt} must have allow_import = 0")

			dp_rows = frappe.db.sql(
				"SELECT `import` FROM `tabDocPerm` WHERE parent = %s AND role IN ('Tracora Admin', 'Tracora Super Admin')",
				(dt,),
				as_dict=True,
			)
			for r in dp_rows:
				self.assertEqual(r.get("import"), 0, f"{dt} DocPerm import must be 0")

		allowed = ["Tracora Asset", "Tracora Software Licence"]
		for dt in allowed:
			allow_import = frappe.db.get_value("DocType", dt, "allow_import")
			self.assertEqual(allow_import, 1, f"{dt} must have allow_import = 1")

	def test_11_patch_is_idempotent(self):
		"""Patch run twice gives identical rows."""
		frappe.set_user("Administrator")
		# Run patch twice
		run_patch()
		rows1 = frappe.db.sql("SELECT role, `read`, `write`, `create`, `delete`, `export` FROM `tabCustom DocPerm` WHERE parent = 'Data Import' ORDER BY role", as_dict=True)
		run_patch()
		rows2 = frappe.db.sql("SELECT role, `read`, `write`, `create`, `delete`, `export` FROM `tabCustom DocPerm` WHERE parent = 'Data Import' ORDER BY role", as_dict=True)
		self.assertEqual(rows1, rows2)
		self.assertEqual(len(rows1), 3)  # System Manager, Tracora Admin, Tracora Super Admin

	def test_12_hooks_registration(self):
		"""FIX 1: Assert every doc_events entry from commit 8bd7572 is still registered
		together with Data Import validate, and permission_query_conditions,
		has_permission, and doctype_js contain their Data Import entries.
		"""
		expected_doc_events = {
			"Employee": {
				"after_insert": "tracora.integrations.hrms.on_employee_change",
				"on_update": "tracora.integrations.hrms.on_employee_change",
				"after_rename": "tracora.integrations.hrms.on_employee_rename",
				"on_trash": "tracora.integrations.hrms.on_hrms_delete",
			},
			"Company": {
				"on_update": "tracora.integrations.hrms.on_company_change",
			},
			"Branch": {
				"on_update": "tracora.integrations.hrms.on_branch_change",
				"after_rename": "tracora.integrations.hrms.on_branch_rename",
			},
			"Department": {
				"on_update": "tracora.integrations.hrms.on_department_change",
			},
		}

		hooks_doc_events = frappe.get_hooks("doc_events")
		for dt, events in expected_doc_events.items():
			self.assertIn(dt, hooks_doc_events, f"DocType {dt} missing from doc_events")
			for event, fn in events.items():
				registered_handlers = hooks_doc_events[dt].get(event, [])
				self.assertIn(fn, registered_handlers, f"Handler {fn} not registered for {dt}.{event}")

		# Data Import validate hook
		self.assertIn("Data Import", hooks_doc_events)
		self.assertIn("tracora.permissions.validate_data_import", hooks_doc_events["Data Import"].get("validate", []))

		# permission_query_conditions
		pqc_hooks = frappe.get_hooks("permission_query_conditions").get("Data Import", [])
		self.assertIn("tracora.permissions.get_data_import_query_conditions", pqc_hooks)

		# has_permission
		hp_hooks = frappe.get_hooks("has_permission").get("Data Import", [])
		self.assertIn("tracora.permissions.has_data_import_permission", hp_hooks)

		# doctype_js
		djs_hooks = frappe.get_hooks("doctype_js").get("Data Import", [])
		self.assertIn("public/js/data_import.js", djs_hooks)

	def test_13_has_permission_tracora_asset_matrix(self):
		"""FIX 2b: Real Data Import doc for Tracora Asset evaluated for S, R, SA, R2, N."""
		doc = frappe.new_doc("Data Import")
		doc.reference_doctype = "Tracora Asset"

		pts = ["read", "write", "create", "delete", "export"]

		# S = only System Manager: all True (same as System Manager Custom DocPerm row)
		frappe.set_user(self.sys_mgr_user)
		s_perms = {pt: frappe.has_permission("Data Import", pt, doc=doc, user=self.sys_mgr_user) for pt in pts}
		self.assertEqual(s_perms, {"read": True, "write": True, "create": True, "delete": True, "export": True})

		# R = only Tracora Admin: read, write, create, export True; delete FALSE
		frappe.set_user(self.admin_user)
		r_perms = {pt: frappe.has_permission("Data Import", pt, doc=doc, user=self.admin_user) for pt in pts}
		self.assertEqual(r_perms, {"read": True, "write": True, "create": True, "delete": False, "export": True})

		# SA = only Tracora Super Admin: read, write, create, export True; delete FALSE
		frappe.set_user(self.super_admin_user)
		sa_perms = {pt: frappe.has_permission("Data Import", pt, doc=doc, user=self.super_admin_user) for pt in pts}
		self.assertEqual(sa_perms, {"read": True, "write": True, "create": True, "delete": False, "export": True})

		# R2 = Tracora Admin and System Manager: same as S (all True)
		frappe.set_user(self.both_user)
		r2_perms = {pt: frappe.has_permission("Data Import", pt, doc=doc, user=self.both_user) for pt in pts}
		self.assertEqual(r2_perms, {"read": True, "write": True, "create": True, "delete": True, "export": True})

		# N = user with no Tracora role and no System Manager (HR User): all False
		frappe.set_user(self.plain_user)
		n_perms = {pt: frappe.has_permission("Data Import", pt, doc=doc, user=self.plain_user) for pt in pts}
		self.assertEqual(n_perms, {"read": False, "write": False, "create": False, "delete": False, "export": False})

	def test_14_has_permission_non_tracora_matrix(self):
		"""FIX 2c: Same checks on a doc with reference_doctype Customer:
		R and SA get False for read and write; S and R2 get what their roles give.
		"""
		doc = frappe.new_doc("Data Import")
		doc.reference_doctype = "Customer"

		# R and SA: False for read and write
		for u in [self.admin_user, self.super_admin_user]:
			frappe.set_user(u)
			self.assertFalse(frappe.has_permission("Data Import", "read", doc=doc, user=u))
			self.assertFalse(frappe.has_permission("Data Import", "write", doc=doc, user=u))
			self.assertFalse(frappe.has_permission("Data Import", "create", doc=doc, user=u))
			self.assertFalse(frappe.has_permission("Data Import", "delete", doc=doc, user=u))

		# S and R2: get what their System Manager role gives (True for read, write, create, delete, export)
		for u in [self.sys_mgr_user, self.both_user]:
			frappe.set_user(u)
			self.assertTrue(frappe.has_permission("Data Import", "read", doc=doc, user=u))
			self.assertTrue(frappe.has_permission("Data Import", "write", doc=doc, user=u))
			self.assertTrue(frappe.has_permission("Data Import", "create", doc=doc, user=u))
			self.assertTrue(frappe.has_permission("Data Import", "delete", doc=doc, user=u))

	def test_15_direct_permission_functions_never_none(self):
		"""FIX 2d: Call has_data_import_permission, get_data_import_query_conditions
		and validate_data_import directly for each user and assert that
		has_data_import_permission never returns None.
		"""
		doc_asset = frappe.new_doc("Data Import")
		doc_asset.reference_doctype = "Tracora Asset"

		doc_cust = frappe.new_doc("Data Import")
		doc_cust.reference_doctype = "Customer"

		doc_empty = frappe.new_doc("Data Import")

		all_users = [self.sys_mgr_user, self.admin_user, self.super_admin_user, self.both_user, self.plain_user]
		pts = ["read", "write", "create", "delete", "export"]

		for u in all_users:
			frappe.set_user(u)

			# get_data_import_query_conditions check
			qc = get_data_import_query_conditions(user=u)
			if u in (self.admin_user, self.super_admin_user):
				self.assertIsNotNone(qc)
				self.assertIn("Tracora", qc)
			else:
				self.assertIsNone(qc)

			# has_data_import_permission checks on all docs and ptypes
			for test_doc in [doc_asset, doc_cust, doc_empty]:
				for pt in pts:
					res = has_data_import_permission(test_doc, ptype=pt, user=u)
					self.assertIsNotNone(res, f"has_data_import_permission returned None for user {u}, doc {test_doc.reference_doctype}, pt {pt}")
					self.assertIsInstance(res, bool, f"has_data_import_permission must return bool, got {type(res)}")

		# validate_data_import directly
		frappe.set_user(self.admin_user)
		validate_data_import(doc_asset)  # allowed, must not raise
		with self.assertRaises(frappe.PermissionError):
			validate_data_import(doc_cust)  # disallowed, must raise PermissionError
		with self.assertRaises(frappe.PermissionError):
			validate_data_import(doc_empty)  # empty reference_doctype must raise PermissionError

		frappe.set_user(self.sys_mgr_user)
		validate_data_import(doc_cust)  # System Manager must not be blocked by hook

	def test_16_insert_data_import_validation_by_user(self):
		"""FIX 2e: Restricted user R inserting for Customer must raise, for Tracora Employee
		must raise, for Tracora Asset and Tracora Software Licence must succeed.
		System Manager S inserting for Customer must NOT be blocked by our hook.
		"""
		frappe.set_user(self.admin_user)

		# Customer raises PermissionError
		with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
			frappe.get_doc({
				"doctype": "Data Import",
				"reference_doctype": "Customer",
				"import_type": "Insert New Records",
			}).insert()

		# Tracora Employee: inserting must raise (blocked by allow_import=0 ValidationError or hook PermissionError)
		with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
			frappe.get_doc({
				"doctype": "Data Import",
				"reference_doctype": "Tracora Employee",
				"import_type": "Insert New Records",
			}).insert()

		# And calling validate_data_import hook directly raises PermissionError
		di_emp = frappe.new_doc("Data Import")
		di_emp.reference_doctype = "Tracora Employee"
		with self.assertRaises(frappe.PermissionError):
			validate_data_import(di_emp)

		# Tracora Asset succeeds
		di_asset = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "Tracora Asset",
			"import_type": "Insert New Records",
		}).insert()
		self.created_docs.append(di_asset)
		self.assertTrue(di_asset.name)

		# Tracora Software Licence succeeds
		di_licence = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "Tracora Software Licence",
			"import_type": "Insert New Records",
		}).insert()
		self.created_docs.append(di_licence)
		self.assertTrue(di_licence.name)

		# System Manager S: validate_data_import does not block Customer
		frappe.set_user(self.sys_mgr_user)
		di_sm_cust = frappe.new_doc("Data Import")
		di_sm_cust.reference_doctype = "Customer"
		# Calling hook directly does not raise
		validate_data_import(di_sm_cust)

	def test_17_get_list_filtering_by_user(self):
		"""FIX 2f: frappe.get_list('Data Import') as R returns only imports whose
		reference_doctype belongs to the Tracora module, and as S returns all.
		"""
		frappe.set_user("Administrator")
		# Create a non-Tracora import
		di_event = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "Event",
			"import_type": "Insert New Records",
		}).insert()
		self.created_docs.append(di_event)

		# Create a Tracora import
		di_asset = frappe.get_doc({
			"doctype": "Data Import",
			"reference_doctype": "Tracora Asset",
			"import_type": "Insert New Records",
		}).insert()
		self.created_docs.append(di_asset)

		# As restricted user R: only Tracora module imports
		frappe.set_user(self.admin_user)
		r_list = frappe.get_list("Data Import", fields=["name", "reference_doctype"])
		r_names = [d.name for d in r_list]
		self.assertIn(di_asset.name, r_names)
		self.assertNotIn(di_event.name, r_names)
		for item in r_list:
			mod = frappe.db.get_value("DocType", item.reference_doctype, "module")
			self.assertEqual(mod, "Tracora")

		# As System Manager S: returns both
		frappe.set_user(self.sys_mgr_user)
		s_list = frappe.get_list("Data Import", fields=["name", "reference_doctype"])
		s_names = [d.name for d in s_list]
		self.assertIn(di_asset.name, s_names)
		self.assertIn(di_event.name, s_names)
