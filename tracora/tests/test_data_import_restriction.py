# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.core.doctype.data_import.data_import import get_import_logs
from tracora.patches.v1_0.restrict_data_import_and_perms import execute as run_patch


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
