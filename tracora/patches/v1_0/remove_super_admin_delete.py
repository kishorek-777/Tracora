import frappe


def execute():
	"""
	Remove delete permission from Tracora Super Admin on all Tracora module doctypes.
	Updates tabDocPerm and tabCustom DocPerm where role = 'Tracora Super Admin'
	and parent is a DocType in module 'Tracora'.
	"""
	tracora_doctypes = frappe.get_all("DocType", filters={"module": "Tracora"}, pluck="name")
	if not tracora_doctypes:
		return

	# 1. Update tabDocPerm
	docperm_to_change = frappe.db.sql(
		"""
		SELECT name, parent FROM `tabDocPerm`
		WHERE role = 'Tracora Super Admin'
		  AND `delete` = 1
		  AND parent IN %(doctypes)s
		""",
		{"doctypes": tuple(tracora_doctypes)},
		as_dict=True,
	)

	if docperm_to_change:
		frappe.db.sql(
			"""
			UPDATE `tabDocPerm`
			SET `delete` = 0
			WHERE role = 'Tracora Super Admin'
			  AND `delete` = 1
			  AND parent IN %(doctypes)s
			""",
			{"doctypes": tuple(tracora_doctypes)},
		)

	# 2. Update tabCustom DocPerm
	custom_to_change = frappe.db.sql(
		"""
		SELECT name, parent FROM `tabCustom DocPerm`
		WHERE role = 'Tracora Super Admin'
		  AND `delete` = 1
		  AND parent IN %(doctypes)s
		""",
		{"doctypes": tuple(tracora_doctypes)},
		as_dict=True,
	)

	if custom_to_change:
		frappe.db.sql(
			"""
			UPDATE `tabCustom DocPerm`
			SET `delete` = 0
			WHERE role = 'Tracora Super Admin'
			  AND `delete` = 1
			  AND parent IN %(doctypes)s
			""",
			{"doctypes": tuple(tracora_doctypes)},
		)

	total_changed = len(docperm_to_change) + len(custom_to_change)
	frappe.logger().info(
		f"remove_super_admin_delete: updated {len(docperm_to_change)} DocPerm row(s) and {len(custom_to_change)} Custom DocPerm row(s) (total: {total_changed})"
	)

	frappe.clear_cache()
