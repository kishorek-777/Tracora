// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tracora Software Licence', {
	setup: function(frm) {
		frm.set_query('company', function() {
			return { filters: {} };
		});
		frm.set_query('user', 'seats', function() {
			return { filters: { status: ['!=', 'Exited'] } };
		});
		frm.set_query('device', 'seats', function() {
			return { filters: { status: ['not in', ['Retired', 'Released']] } };
		});
	},

	refresh: function(frm) {
		frm.trigger('toggle_seats_user_reqd');
		frm.trigger('render_overdue_banner');

		if (!frm.is_new()) {
			const status_colors = {
				'Active': 'green',
				'Unassigned': 'blue',
				'Expired': 'red'
			};
			frm.page.set_indicator(__(frm.doc.licence_status), status_colors[frm.doc.licence_status] || 'grey');
		}
	},

	licence_type: function(frm) {
		frm.trigger('toggle_seats_user_reqd');
	},

	toggle_seats_user_reqd: function(frm) {
		const is_user_licence = frm.doc.licence_type === 'User licence';
		frm.fields_dict.seats.grid.toggle_reqd('user', is_user_licence);
		frm.fields_dict.seats.grid.refresh();
	},

	render_overdue_banner: function(frm) {
		if (frm.doc.licence_expiry_date) {
			const diff = frappe.datetime.get_diff(frm.doc.licence_expiry_date, frappe.datetime.get_today());
			if (diff < 0) {
				frm.set_intro(__('⚠️ This licence has expired (expired on {0}). Overdue notice flagged.', [frappe.datetime.str_to_user(frm.doc.licence_expiry_date)]), 'red');
			}
		}
	}
});
