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
				if (frappe.query_report && typeof frappe.query_report.toggle_contextual_filters === "function") {
					frappe.query_report.toggle_contextual_filters();
				}
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

	onload: function(report) {
		report.toggle_contextual_filters = function() {
			const view = report.get_filter_value("primary_view") || "Assets Owned";
			const is_licence = (view === "Licence Expiry" || view === "Licence Renewal Due");
			const is_emp_view = (view === "Assets by Employee");
			const is_external = (view === "External Custody");

			// 1. Licence filters
			["licence_type", "renewal_cycle", "include_non_renewing"].forEach(fn => {
				const f = report.get_filter(fn);
				if (f && f.$wrapper) {
					f.df.hidden = is_licence ? 0 : 1;
					f.$wrapper.toggle(Boolean(is_licence));
					if (!is_licence && typeof f.set_value === "function" && f.get_value && f.get_value()) {
						if (fn === "include_non_renewing") {
							f.set_value(0);
						} else {
							f.set_value("");
						}
					}
				}
			});

			// 2. Hardware Asset Status & Condition filters
			["status", "condition"].forEach(fn => {
				const f = report.get_filter(fn);
				if (f && f.$wrapper) {
					const show = !is_licence;
					f.df.hidden = show ? 0 : 1;
					f.$wrapper.toggle(Boolean(show));
					if (!show && typeof f.set_value === "function" && f.get_value && f.get_value()) {
						f.set_value([]);
					}
				}
			});

			// 3. Branch & Department filters
			["branch", "department"].forEach(fn => {
				const f = report.get_filter(fn);
				if (f && f.$wrapper) {
					const show = !is_licence && !is_external;
					f.df.hidden = show ? 0 : 1;
					f.$wrapper.toggle(Boolean(show));
					if (!show && typeof f.set_value === "function" && f.get_value && f.get_value()) {
						f.set_value([]);
					}
				}
			});

			// 4. Employee filter: only relevant for "Assets by Employee"
			const emp_filter = report.get_filter("employee");
			if (emp_filter && emp_filter.$wrapper) {
				const show = is_emp_view;
				emp_filter.df.hidden = show ? 0 : 1;
				emp_filter.$wrapper.toggle(Boolean(show));
				if (!show && typeof emp_filter.set_value === "function" && emp_filter.get_value && emp_filter.get_value()) {
					emp_filter.set_value("");
				}
			}
		};

		// Run immediately and after DOM stabilizes
		report.toggle_contextual_filters();
		setTimeout(() => {
			if (typeof report.toggle_contextual_filters === "function") {
				report.toggle_contextual_filters();
			}
		}, 100);
	},

	after_refresh: function(report) {
		if (report && typeof report.toggle_contextual_filters === "function") {
			report.toggle_contextual_filters();
		}
	},

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
