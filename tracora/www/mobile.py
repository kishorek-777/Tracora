from pathlib import Path

import frappe


def get_context(context):
	# FR-35: Serves the dedicated Tracora Mobile PWA directly for both guest and authenticated users.
	# Guaranteed zero cross-user caching across Frappe page cache, reverse proxies, and CDN.
	context.no_cache = 1
	frappe.local.no_cache = 1
	frappe.local.response_headers.update(
		{
			"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0, private",
			"Pragma": "no-cache",
			"Vary": "Cookie, Accept-Encoding",
		}
	)

	html_file = Path(frappe.get_app_path("tracora", "public", "frontend", "mobile.html"))
	if html_file.exists():
		raw_html = html_file.read_text(encoding="utf-8")
		user = frappe.session.user if frappe.session.user != "Guest" else None
		csrf_token = frappe.sessions.get_csrf_token()
		bootstrap_script = (
			f"<script>\n"
			f"\twindow.__TRACORA_USER__ = {frappe.as_json(user)};\n"
			f"\twindow.__CSRF_TOKEN__ = {frappe.as_json(csrf_token)};\n"
			f"</script>\n"
		)
		if "</head>" in raw_html:
			context.frontend_html = raw_html.replace("</head>", f"{bootstrap_script}</head>", 1)
		else:
			context.frontend_html = f"{bootstrap_script}{raw_html}"
	else:
		context.frontend_html = "<h1>Tracora Mobile PWA Not Built</h1>"
	return context
