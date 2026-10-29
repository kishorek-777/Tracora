// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.listview_settings['Tracora Vendor'] = {
	add_fields: ['status', 'vendor_category', 'primary_email', 'primary_phone', 'city'],
	get_indicator: function(doc) {
		const colors = {
			'Active': 'green',
			'Inactive': 'red'
		};
		return [__(doc.status), colors[doc.status] || 'grey', 'status,=,' + doc.status];
	},
	formatters: {
		vendor_category: function(value) {
			if (!value) return '';
			return `<span class="indicator-pill blue">${frappe.utils.escape_html(value)}</span>`;
		}
	}
};

