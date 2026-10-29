// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tracora Asset Audit Log', {
	setup: function(frm) {
		frm.set_query('asset', function() {
			return { filters: {} };
		});
	},

	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.disable_save();
			frm.set_read_only();
		}
	}
});
