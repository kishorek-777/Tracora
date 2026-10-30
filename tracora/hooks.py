app_name = "tracora"
app_title = "IT Asset Intelligence"
app_publisher = "Kishore"
app_description = "Asset custody register"
app_email = "kishore.k@aionioncapital.com"
app_license = "mit"
app_logo_url = "/assets/tracora/images/tracora_icon.svg"

# Website routing for custom SPA portal & mobile PWA
website_route_rules = [
	{"from_route": "/tracora/<path:app_path>", "to_route": "tracora"},
	{"from_route": "/tracora", "to_route": "tracora"},
	{"from_route": "/mobile/<path:app_path>", "to_route": "mobile"},
	{"from_route": "/mobile", "to_route": "mobile"},
]

# Desk JS includes with cache busting
app_include_js = [
	"/assets/tracora/js/tracora.js?v=2.8.0",
	"/assets/tracora/js/tracora_quick_ops.js?v=2.8.0",
]
app_include_css = "/assets/tracora/css/tracora.css?v=2.8.0"

# Doc events for external apps (HRMS / ERPNext)
doc_events = {
	"Data Import": {
		"validate": "tracora.permissions.validate_data_import",
	},

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

# Jinja methods
jenv = {
	"methods": [
		"qr_base64:tracora.tags.qr.qr_base64",
	]
}

# Fixtures
fixtures = [
	{
		"dt": "Role",
		"filters": [["name", "in", ["Tracora Super Admin", "Tracora Admin"]]],
	},
	{
		"dt": "Print Format",
		"filters": [["name", "in", ["Tracora Asset Label"]]],
	},
]

# Scheduled Events
scheduler_events = {
	"daily": [
		"tracora.licences.status.recalculate_next_renewal_dates",
		"tracora.licences.status.mark_expired_licences",
		"tracora.reminders.scheduler.run_daily_reminders",
	],
	"hourly": [
		"tracora.licences.status.mark_expired_licences",
	],
}


# Permission hooks
permission_query_conditions = {
	"Data Import": "tracora.permissions.get_data_import_query_conditions",
}

has_permission = {
	"Data Import": "tracora.permissions.has_data_import_permission",
	"Tracora Asset Audit Log": "tracora.permissions.has_asset_audit_log_permission",
}

doctype_js = {
	"Data Import": "public/js/data_import.js",
}
