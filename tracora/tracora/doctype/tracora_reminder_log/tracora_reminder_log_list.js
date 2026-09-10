// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.listview_settings['Tracora Reminder Log'] = {
	add_fields: ['delivery_status', 'reminder_type', 'sent_on', 'due_date', 'days_before', 'recipient'],
	get_indicator: function(doc) {
		if (doc.delivery_status === 'Sent') {
			return [__('Sent'), 'green', 'delivery_status,=,Sent'];
		} else if (doc.delivery_status === 'Queued') {
			return [__('Queued'), 'blue', 'delivery_status,=,Queued'];
		} else if (doc.delivery_status === 'Failed') {
			return [__('Failed'), 'red', 'delivery_status,=,Failed'];
		}
		return [__(doc.delivery_status || 'Unknown'), 'gray', ''];
	}
};
