// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.provide('tracora');

tracora.check_scheduler_health = function() {
	if (!frappe.session || frappe.session.user === 'Guest') return;

	frappe.call({
		method: 'tracora.reminders.scheduler.check_scheduler_health',
		callback: function(r) {
			if (!r || !r.message) return;
			const data = r.message;
			$('#tracora-scheduler-health-banner').remove();

			const msgs = [];
			if (data.is_stale && data.stale_message) {
				msgs.push(data.stale_message);
			}
			if (data.no_recipients && data.recipient_message) {
				msgs.push(data.recipient_message);
			}

			if (msgs.length > 0) {
				const alertHtml = `
					<div id="tracora-scheduler-health-banner" class="alert alert-warning" role="alert" style="margin: 15px 20px 0 20px; border-left: 4px solid #f6ad55; font-size: 13px;">
						<div style="display: flex; align-items: center; justify-content: space-between;">
							<div>
								<strong>⚠️ Tracora Reminder System Notice:</strong>
								<ul style="margin: 4px 0 0 18px; padding: 0;">
									${msgs.map(m => `<li>${frappe.utils.escape_html(m)}</li>`).join('')}
								</ul>
							</div>
							<button type="button" class="close" data-dismiss="alert" aria-label="Close" style="font-size: 18px; line-height: 1;">
								<span aria-hidden="true">&times;</span>
							</button>
						</div>
					</div>
				`;
				// Append to page head or container if on Tracora workspace
				const currentRoute = frappe.get_route_str();
				if (currentRoute.includes('tracora') || currentRoute === 'workspaces') {
					$('.layout-main-section').first().prepend(alertHtml);
				}
			}
		}
	});
};

$(document).on('page-change', function() {
	const route = frappe.get_route_str();
	if (route.includes('tracora') || route.startsWith('workspaces')) {
		tracora.check_scheduler_health();
	}
});
