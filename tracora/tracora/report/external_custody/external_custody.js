// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.query_reports["External Custody"] = {
	filters: [
		{
			fieldname: "holding_company",
			label: __("External Company"),
			fieldtype: "Link",
			options: "Tracora Company",
			get_query: () => {
				return {
					filters: { "company_type": "External" }
				};
			}
		},
		{
			fieldname: "employee",
			label: __("External Employee"),
			fieldtype: "Link",
			options: "Tracora Employee"
		}
	],
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "status" && data) {
			const color = data.status === "Assigned" ? "green" : "orange";
			return `<span class="indicator-pill ${color}">${data.status}</span>`;
		}
		return value;
	}
};
