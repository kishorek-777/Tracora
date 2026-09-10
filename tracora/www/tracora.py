import frappe
from pathlib import Path

def get_context(context):
	context.no_cache = 1
	html_file = Path(frappe.get_app_path("tracora", "public", "frontend", "index.html"))
	if html_file.exists():
		context.frontend_html = html_file.read_text(encoding="utf-8")
	else:
		context.frontend_html = "<h1>Tracora Frontend Not Found</h1>"
	return context
