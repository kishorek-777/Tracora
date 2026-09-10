// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.query_reports["Assets by Employee"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Internal Company"),
			fieldtype: "Link",
			options: "Tracora Company",
			get_query: () => {
				return {
					filters: { "company_type": "Internal" }
				};
			}
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Tracora Department"
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Tracora Employee"
		}
	],
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "employee_status" && data) {
			if (data.employee_status === "Exited") {
				return `<span class="indicator-pill red" style="font-weight: 600;">Exited (Custody Alert)</span>`;
			}
			const color = data.employee_status === "Active" ? "green" : "orange";
			return `<span class="indicator-pill ${color}">${data.employee_status}</span>`;
		}
		if (column.fieldname === "status" && data) {
			const color = data.status === "Assigned" ? "green" : "orange";
			return `<span class="indicator-pill ${color}">${data.status}</span>`;
		}
		return value;
	}
};
