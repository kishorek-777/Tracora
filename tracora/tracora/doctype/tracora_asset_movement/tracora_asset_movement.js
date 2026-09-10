// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tracora Asset Movement', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.disable_save();
		}
	},
});
