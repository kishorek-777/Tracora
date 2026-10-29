# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from tracora.tracora.doctype.tracora_infra_record_type.tracora_infra_record_type import FALLBACK_TYPE


def _escape_like_pattern(text: str) -> str:
	"""
	Escape backslash, percent, and underscore characters for SQL LIKE clauses
	so user query terms act as literal strings rather than wildcards.
	"""
	return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@frappe.whitelist()
def search_records(
	query: str = "",
	record_type: str | None = None,
	category: str | None = None,
	start: int = 0,
	page_length: int = 20,
) -> dict:
	frappe.has_permission("Tracora Infra Record", "read", throw=True)

	try:
		start = int(start)
	except (ValueError, TypeError):
		start = 0
	if start < 0:
		start = 0

	try:
		page_length = int(page_length)
	except (ValueError, TypeError):
		page_length = 20
	if page_length < 1:
		page_length = 1
	elif page_length > 100:
		page_length = 100

	if record_type:
		record_type = str(record_type).strip()
		if record_type:
			if not frappe.db.exists("Tracora Infra Record Type", record_type):
				frappe.throw(
					_("Record Type '{0}' does not exist.").format(record_type),
					frappe.ValidationError,
				)
		else:
			record_type = None
	else:
		record_type = None

	if category:
		category = str(category).strip() or None
	else:
		category = None

	conditions = ["1=1"]
	values = []

	if record_type:
		conditions.append("record_type = %s")
		values.append(record_type)

	if category:
		conditions.append("category = %s")
		values.append(category)

	if query and str(query).strip():
		words = str(query).strip().split()
		for word in words:
			if word:
				escaped = _escape_like_pattern(word.lower())
				conditions.append("(LOWER(search_text) LIKE %s OR LOWER(name) LIKE %s OR LOWER(title) LIKE %s)")
				pattern = f"%{escaped}%"
				values.extend([pattern, pattern, pattern])

	where_clause = " AND ".join(conditions)

	total = frappe.db.sql(
		f"SELECT COUNT(*) FROM `tabTracora Infra Record` WHERE {where_clause}",
		tuple(values),
	)[0][0]

	records_sql = f"""
		SELECT name, title, record_type, category, modified
		FROM `tabTracora Infra Record`
		WHERE {where_clause}
		ORDER BY modified DESC
		LIMIT %s OFFSET %s
	"""
	records = frappe.db.sql(records_sql, tuple(values + [page_length, start]), as_dict=True)

	return {
		"records": records,
		"total": total,
	}


@frappe.whitelist()
def get_counts() -> list[dict]:
	frappe.has_permission("Tracora Infra Record", "read", throw=True)

	grouped_counts = frappe.db.sql(
		"""
		SELECT record_type, COUNT(*) AS cnt
		FROM `tabTracora Infra Record`
		GROUP BY record_type
		""",
		as_dict=True,
	)

	counts_map = {}
	for row in grouped_counts:
		rt = row.record_type
		count = row.cnt
		if not rt:
			rt = FALLBACK_TYPE
		counts_map[rt] = counts_map.get(rt, 0) + count

	types = frappe.db.get_all(
		"Tracora Infra Record Type",
		fields=["name", "type_name", "sort_order"],
		order_by="sort_order ASC, name ASC",
	)

	result = []
	for t in types:
		result.append({
			"record_type": t.name,
			"label": t.type_name or t.name,
			"count": counts_map.get(t.name, 0),
		})

	return result
