// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.query_reports["Assets Owned"] = {
	filters: [
		{
			fieldname: "owner_company",
			label: __("Owner Company"),
			fieldtype: "Link",
			options: "Tracora Company"
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nIn Store\nAssigned\nUnder Maintenance\nRecovered\nRetired\nDisposed\nLost\nIn Transit"
		},
		{
			fieldname: "condition",
			label: __("Condition"),
			fieldtype: "Select",
			options: "\nNew\nGood\nFair\nPoor\nBroken"
		}
	],
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "status" && data) {
			const colorMap = {
				"In Store": "blue",
				"Assigned": "green",
				"Under Maintenance": "orange",
				"Recovered": "cyan",
				"Retired": "gray",
				"Disposed": "darkgray",
				"Lost": "red",
				"In Transit": "purple"
			};
			const color = colorMap[data.status] || "gray";
			return `<span class="indicator-pill ${color}">${data.status}</span>`;
		}
		return value;
	}
};
