// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.query_reports["Licence Expiry"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Tracora Company"
		},
		{
			fieldname: "licence_type",
			label: __("Licence Type"),
			fieldtype: "Select",
			options: "\nUser licence\nDevice licence"
		},
		{
			fieldname: "licence_status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nActive\nUnassigned\nExpired",
			default: "Active"
		}
	],
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "days_remaining" && data && data.days_remaining != null) {
			const days = data.days_remaining;
			let color = "green";
			if (days < 0) {
				color = "red";
				return `<span class="indicator-pill red" style="font-weight: 600;">Expired (${Math.abs(days)}d ago)</span>`;
			} else if (days < 7) {
				color = "red";
			} else if (days < 30) {
				color = "orange";
			}
			return `<span class="indicator-pill ${color}">${days} days</span>`;
		}
		if (column.fieldname === "licence_status" && data) {
			const color = data.licence_status === "Active" ? "green" : (data.licence_status === "Expired" ? "red" : "gray");
			return `<span class="indicator-pill ${color}">${data.licence_status}</span>`;
		}
		return value;
	}
};
