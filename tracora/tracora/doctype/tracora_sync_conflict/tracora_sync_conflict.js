// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tracora Sync Conflict", {
	refresh: function(frm) {
		if (frm.doc.conflict_status === "Open") {
			frm.add_custom_button(__("Resolve Conflict"), function() {
				frappe.confirm(
					__("Mark this sync conflict as Resolved after reconciling the Tracora record?"),
					function() {
						frm.call({
							doc: frm.doc,
							method: "resolve",
							freeze: true,
							callback: function(r) {
								frappe.show_alert({ message: __("Conflict marked as Resolved"), indicator: "green" });
								frm.reload_doc();
							}
						});
					}
				);
			}).addClass("btn-primary");
		}
		frm.trigger("render_comparison");
	},

	render_comparison: function(frm) {
		if (!frm.doc.hrms_values || !frm.doc.tracora_values) return;
		let hrms = {};
		let tracora = {};
		try {
			hrms = typeof frm.doc.hrms_values === "string" ? JSON.parse(frm.doc.hrms_values) : frm.doc.hrms_values;
		} catch (e) {}
		try {
			tracora = typeof frm.doc.tracora_values === "string" ? JSON.parse(frm.doc.tracora_values) : frm.doc.tracora_values;
		} catch (e) {}

		let all_keys = Array.from(new Set([...Object.keys(hrms), ...Object.keys(tracora)]));
		if (!all_keys.length) return;

		let differing = (frm.doc.differing_fields || "").split(",").map(s => s.trim());

		let html = '<div class="comparison-wrapper" style="margin-bottom: 20px;">' +
			'<div style="font-weight: bold; margin-bottom: 8px;">' + __("Side-by-Side Field Comparison") + '</div>' +
			'<table class="table table-bordered table-sm" style="background: var(--card-bg, #fff);">' +
			'<thead><tr>' +
			'<th style="width: 30%;">' + __("Field") + '</th>' +
			'<th style="width: 35%; color: #0284c7;">' + __("HRMS Value") + '</th>' +
			'<th style="width: 35%; color: #16a34a;">' + __("Tracora Value") + '</th>' +
			'</tr></thead><tbody>';

		all_keys.forEach(key => {
			let is_diff = differing.includes(key) || hrms[key] !== tracora[key];
			let row_style = is_diff ? 'background-color: var(--alert-bg-warning, #fffbeb); font-weight: 500;' : '';
			html += '<tr style="' + row_style + '">' +
				'<td>' + frappe.utils.escape_html(key) + (is_diff ? ' <span class="badge badge-warning">Mismatch</span>' : '') + '</td>' +
				'<td>' + frappe.utils.escape_html(String(hrms[key] ?? "")) + '</td>' +
				'<td>' + frappe.utils.escape_html(String(tracora[key] ?? "")) + '</td>' +
				'</tr>';
		});

		html += '</tbody></table></div>';
		frm.dashboard.set_headline(html);
	}
});
