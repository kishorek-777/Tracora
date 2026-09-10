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
		frm.trigger('render_flagged_seats_banner');
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

	render_flagged_seats_banner: function(frm) {
		const flagged_seats = (frm.doc.seats || []).filter(s => s.seat_status === 'Flagged');
		if (flagged_seats.length > 0) {
			const seat_items = flagged_seats.map(s => {
				const user_str = s.user ? ` (${frappe.utils.escape_html(s.user)})` : '';
				const reason_str = s.flagged_reason ? ` &mdash; <i>${frappe.utils.escape_html(s.flagged_reason)}</i>` : '';
				return `<li>Device <b>${frappe.utils.escape_html(s.device)}</b>${user_str}${reason_str}</li>`;
			}).join('');

			const msg = `
				<div style="font-size: 13px;">
					<strong>⚠️ ${flagged_seats.length} seat${flagged_seats.length > 1 ? 's' : ''} need attention &mdash; the device was unassigned or retired.</strong>
					<ul style="margin-top: 4px; margin-bottom: 0; padding-left: 18px;">
						${seat_items}
					</ul>
				</div>
			`;
			frm.dashboard.set_headline(msg, 'orange');
		} else {
			frm.dashboard.clear_headline();
		}
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
