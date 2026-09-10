// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.query_reports["Licence Renewal Due"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Tracora Company"
		},
		{
			fieldname: "renewal_cycle",
			label: __("Renewal Cycle"),
			fieldtype: "Select",
			options: "\nMonthly\nQuarterly\nHalf-yearly\nYearly\nOne-time"
		},
		{
			fieldname: "include_non_renewing",
			label: __("Include Non-Renewing / Unset Start Date"),
			fieldtype: "Check",
			default: 0
		}
	],
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "days_until_renewal" && data) {
			if (data.days_until_renewal == null) {
				return `<span style="color: #a0aec0; font-style: italic;">Non-Renewing</span>`;
			}
			const days = data.days_until_renewal;
			let color = "green";
			if (days < 0) {
				color = "red";
				return `<span class="indicator-pill red" style="font-weight: 600;">Renewal Due (${Math.abs(days)}d ago)</span>`;
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
