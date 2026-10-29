// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.listview_settings['Tracora Software Licence'] = {
	add_fields: ['licence_status', 'licence_expiry_date', 'licence_start_date', 'renewal_cycle', 'next_renewal_date', 'licence_type', 'software_name', 'licence_name'],
	get_indicator: function(doc) {
		const diff = doc.licence_expiry_date ? frappe.datetime.get_diff(doc.licence_expiry_date, frappe.datetime.get_today()) : 999;
		if (diff < 0 || doc.licence_status === 'Expired') {
			return [__('Expired'), 'red', 'licence_status,=,Expired'];
		}
		if (doc.licence_status === 'Active') {
			return [__('Active'), 'green', 'licence_status,=,Active'];
		}
		return [__('Unassigned'), 'blue', 'licence_status,=,Unassigned'];
	},
	formatters: {
		licence_expiry_date: function(value, df, doc) {
			if (!value) return '';
			const diff = frappe.datetime.get_diff(value, frappe.datetime.get_today());
			const formatted_date = frappe.datetime.str_to_user(value);
			if (diff < 0) {
				return `<span>${formatted_date}</span> <span class="indicator-pill red">${Math.abs(diff)}d ago</span>`;
			} else if (diff < 7) {
				return `<span>${formatted_date}</span> <span class="indicator-pill red">${diff}d left</span>`;
			} else if (diff <= 30) {
				return `<span>${formatted_date}</span> <span class="indicator-pill orange">${diff}d left</span>`;
			}
			return `<span>${formatted_date}</span> <span class="indicator-pill green">${diff}d left</span>`;
		},
		next_renewal_date: function(value, df, doc) {
			if (!value) {
				if (doc.renewal_cycle === 'One-time') {
					return `<span class="text-muted" style="font-size: 11px;">${__('N/A (One-time)')}</span>`;
				}
				if (!doc.licence_start_date) {
					return `<span class="indicator-pill orange" style="font-size: 11px;" title="${__('Missing Start Date')}">${__('No Start Date')}</span>`;
				}
				return '<span class="text-muted">-</span>';
			}
			const diff = frappe.datetime.get_diff(value, frappe.datetime.get_today());
			const formatted_date = frappe.datetime.str_to_user(value);
			if (diff < 0) {
				return `<span>${formatted_date}</span> <span class="indicator-pill red">${Math.abs(diff)}d overdue</span>`;
			} else if (diff <= 30) {
				return `<span>${formatted_date}</span> <span class="indicator-pill orange">In ${diff}d</span>`;
			}
			return `<span>${formatted_date}</span>`;
		}
	}
};
