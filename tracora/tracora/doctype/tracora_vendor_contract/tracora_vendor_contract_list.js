// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.listview_settings['Tracora Vendor Contract'] = {
	add_fields: ['renewal_status', 'expected_amount', 'currency', 'renewal_frequency', 'next_renewal_date', 'vendor', 'contract_title'],
	get_indicator: function(doc) {
		const colors = {
			'Active': 'green',
			'Renewal Due': 'orange',
			'Overdue': 'red',
			'Completed': 'grey',
			'Terminated': 'grey'
		};
		return [__(doc.renewal_status), colors[doc.renewal_status] || 'grey', 'renewal_status,=,' + doc.renewal_status];
	},
	formatters: {
		next_renewal_date: function(value, df, doc) {
			if (!value) return '';
			const today = frappe.datetime.get_today();
			const diff = frappe.datetime.get_diff(value, today);
			let badge = '';

			if (diff < 0) {
				badge = `<span class="indicator-pill red" style="margin-left: 6px;">${Math.abs(diff)}d overdue</span>`;
			} else if (diff === 0) {
				badge = `<span class="indicator-pill orange" style="margin-left: 6px;">Due Today</span>`;
			} else if (diff <= 30) {
				badge = `<span class="indicator-pill orange" style="margin-left: 6px;">In ${diff}d</span>`;
			}
			return `<span>${frappe.datetime.str_to_user(value)}</span>${badge}`;
		},
		expected_amount: function(value, df, doc) {
			if (!value) return '';
			const curr = doc.currency || 'INR';
			return `<strong>${format_currency(value, curr)}</strong>`;
		}
	}
};

