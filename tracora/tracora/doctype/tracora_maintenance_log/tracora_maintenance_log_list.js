// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.listview_settings['Tracora Maintenance Log'] = {
	add_fields: ['log_status', 'asset', 'vendor', 'date_sent', 'due_date', 'date_returned'],
	get_indicator: function(doc) {
		const colors = {
			'Open': 'orange',
			'Closed': 'green',
			'Beyond Repair': 'red'
		};
		return [__(doc.log_status), colors[doc.log_status] || 'grey', 'log_status,=,' + doc.log_status];
	},
	formatters: {
		asset: function(value) {
			if (!value) return '';
			return `<span class="tracora-tag-pill">${frappe.utils.escape_html(value)}</span>`;
		},
		due_date: function(value, df, doc) {
			if (!value) return '';
			if (doc.log_status === 'Open') {
				const today = frappe.datetime.get_today();
				const diff = frappe.datetime.get_diff(value, today);
				if (diff < 0) {
					return `<span>${frappe.datetime.str_to_user(value)}</span> <span class="indicator-pill red">${Math.abs(diff)}d overdue</span>`;
				} else if (diff <= 3) {
					return `<span>${frappe.datetime.str_to_user(value)}</span> <span class="indicator-pill orange">${diff}d left</span>`;
				}
			}
			return `<span>${frappe.datetime.str_to_user(value)}</span>`;
		}
	}
};

