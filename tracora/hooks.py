app_name = "tracora"
app_title = "Tracora"
app_publisher = "Kishore"
app_description = "Asset custody register"
app_email = "kishore.k@aionioncapital.com"
app_license = "mit"

# Website routing for custom SPA portal & mobile PWA
website_route_rules = [
	{"from_route": "/tracora/<path:app_path>", "to_route": "tracora"},
	{"from_route": "/tracora", "to_route": "tracora"},
	{"from_route": "/mobile/<path:app_path>", "to_route": "mobile"},
	{"from_route": "/mobile", "to_route": "mobile"},
]

# Doc events for external apps (HRMS / ERPNext)
doc_events = {
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


# Desk JS includes
app_include_js = "/assets/tracora/js/tracora.js"
