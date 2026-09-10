// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.query_reports["Tracora Report"] = {
	filters: [
		{
			fieldname: "primary_view",
			label: __("Report View"),
			fieldtype: "Select",
			options: [
				"Assets Owned",
				"Assets Held",
				"Assets by Branch",
				"Assets by Department",
				"Assets by Employee",
				"External Custody",
				"Licence Expiry",
				"Licence Renewal Due"
			].join("\n"),
			default: "Assets Owned",
			reqd: 1,
			on_change: function() {
				frappe.query_report.refresh();
			}
		},
		{
			fieldname: "company",
			label: __("Companies"),
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options("Tracora Company", txt).then(r => r || []);
			}
		},
		{
			fieldname: "branch",
			label: __("Branches"),
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options("Tracora Branch", txt).then(r => r || []);
			}
		},
		{
			fieldname: "department",
			label: __("Departments"),
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options("Tracora Department", txt).then(r => r || []);
			}
		},
		{
			fieldname: "status",
			label: __("Asset Statuses"),
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				const statuses = ["In Store", "Assigned", "Under Maintenance", "Retired", "Disposed", "Lost"];
				return statuses
					.filter(s => s.toLowerCase().includes((txt || "").toLowerCase()))
					.map(s => ({ value: s, label: s, description: s }));
			}
		},
		{
			fieldname: "condition",
			label: __("Conditions"),
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				const conditions = ["New", "Good", "Fair", "Poor", "Damaged"];
				return conditions
					.filter(c => c.toLowerCase().includes((txt || "").toLowerCase()))
					.map(c => ({ value: c, label: c, description: c }));
			}
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Tracora Employee"
		},
		{
			fieldname: "licence_type",
			label: __("Licence Type"),
			fieldtype: "Select",
			options: "\nUser licence\nDevice licence"
		},
		{
			fieldname: "renewal_cycle",
			label: __("Renewal Cycle"),
			fieldtype: "Select",
			options: "\nMonthly\nQuarterly\nYearly\nOne-time"
		},
		{
			fieldname: "include_non_renewing",
			label: __("Include Non-Renewing / Unset Start Date"),
			fieldtype: "Check",
			default: 0
		},
		{
			fieldname: "selected_columns",
			label: __("Filter Columns"),
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				if (!frappe.query_report || !frappe.query_report.columns || !Array.isArray(frappe.query_report.columns)) {
					return [];
				}
				return frappe.query_report.columns
					.filter(c => c && c.label && c.label.toLowerCase().includes((txt || "").toLowerCase()))
					.map(c => ({ value: c.fieldname, label: c.label, description: c.fieldname }));
			}
		}
	],

	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "status" && data && data.status) {
			const color_map = {
				"In Store": "blue",
				"Assigned": "green",
				"Under Maintenance": "orange",
				"Retired": "gray",
				"Disposed": "darkgray",
				"Lost": "red"
			};
			const c = color_map[data.status] || "blue";
			return `<span class="indicator-pill ${c}">${value}</span>`;
		}

		if (column.fieldname === "employee_status" && data && data.employee_status) {
			if (data.employee_status === "Exited") {
				return `<span class="indicator-pill red" style="font-weight: bold;">Exited (Custody Alert)</span>`;
			}
			return `<span class="indicator-pill green">${value}</span>`;
		}

		if ((column.fieldname === "days_remaining" || column.fieldname === "days_until_renewal") && value != null) {
			const days = Number(data[column.fieldname]);
			if (!isNaN(days)) {
				let color = "green";
				if (days < 7) {
					color = "red";
				} else if (days < 30) {
					color = "orange";
				}
				return `<span class="indicator-pill ${color}" style="font-weight: 600;">${days} days</span>`;
			}
		}

		return value;
	}
};
