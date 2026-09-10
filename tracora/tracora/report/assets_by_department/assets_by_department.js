// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.query_reports["Assets by Department"] = {
	filters: [
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Tracora Department"
		},
		{
			fieldname: "holding_company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Tracora Company"
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
		if (column.fieldname === "department" && data && data.department === "Unassigned Stock") {
			return `<span style="font-weight: bold; color: #718096;">Unassigned Stock</span>`;
		}
		return value;
	}
};
