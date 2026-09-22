import frappe
from pathlib import Path


def get_context(context):
	# FR-35: Login is required. Unauthenticated access is redirected to login.
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/mobile"
		raise frappe.Redirect

	context.no_cache = 1
	html_file = Path(frappe.get_app_path("tracora", "public", "frontend", "mobile.html"))
	if html_file.exists():
		context.frontend_html = html_file.read_text(encoding="utf-8")
	else:
		context.frontend_html = "<h1>Tracora Mobile PWA Not Built</h1>"
	return context
