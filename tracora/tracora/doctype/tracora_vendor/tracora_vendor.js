// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tracora Vendor', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('View Contracts'), function() {
				frappe.set_route('List', 'Tracora Vendor Contract', { vendor: frm.doc.name });
			}, __('Actions'));

			frm.add_custom_button(__('Create Contract'), function() {
				frappe.new_doc('Tracora Vendor Contract', { vendor: frm.doc.name });
			}, __('Actions'));
		}
	}
});

