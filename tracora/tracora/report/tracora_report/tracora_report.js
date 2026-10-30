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

	get_datatable_options: function(options) {
		return Object.assign(options || {}, {
			inlineFilters: false
		});
	},

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

		if (!report.page.has_chart_toggle) {
			report.page.has_chart_toggle = true;
			report.page.add_inner_button(__('📊 Toggle Chart'), function() {
				if (report.$chart) {
					report.$chart.toggle();
				}
			}, __('Actions'));
		}
	},

	after_refresh: function(report) {
		if (report && typeof report.toggle_contextual_filters === "function") {
			report.toggle_contextual_filters();
		}

		// Keep the datatable prominently in focus: hide bulky chart by default
		if (report.$chart && report.$chart.length) {
			report.$chart.hide();
		}

		// Executive KPI Summary Cards
		if (report && report.$summary && report.data && Array.isArray(report.data)) {
			report.$summary.empty();
			const view = report.get_filter_value("primary_view") || "Assets Owned";
			const data = report.data;
			const total_count = data.length;
			const summaries = [];

			if (view === "Licence Expiry" || view === "Licence Renewal Due") {
				const exp_30 = data.filter(d => {
					const days = Number(d.days_remaining ?? d.days_until_renewal);
					return !isNaN(days) && days <= 30;
				}).length;
				const exp_90 = data.filter(d => {
					const days = Number(d.days_remaining ?? d.days_until_renewal);
					return !isNaN(days) && days > 30 && days <= 90;
				}).length;

				summaries.push({
					value: total_count,
					indicator: "Indigo",
					label: __("Tracked Licences"),
					datatype: "Int"
				});
				summaries.push({
					value: exp_30,
					indicator: exp_30 > 0 ? "Red" : "Green",
					label: __("Expiring ≤ 30 Days"),
					datatype: "Int"
				});
				summaries.push({
					value: exp_90,
					indicator: exp_90 > 0 ? "Orange" : "Blue",
					label: __("Expiring in 31–90 Days"),
					datatype: "Int"
				});
			} else if (view === "Assets by Employee") {
				const exited_alerts = data.filter(d => d.employee_status === "Exited").length;
				const unique_emps = new Set(data.map(d => d.employee).filter(Boolean)).size;

				summaries.push({
					value: total_count,
					indicator: "Indigo",
					label: __("Assets in Custody"),
					datatype: "Int"
				});
				summaries.push({
					value: unique_emps,
					indicator: "Green",
					label: __("Active Custodians"),
					datatype: "Int"
				});
				summaries.push({
					value: exited_alerts,
					indicator: exited_alerts > 0 ? "Red" : "Green",
					label: __("Exited Employee Alerts"),
					datatype: "Int"
				});
			} else if (view === "External Custody") {
				const unique_holders = new Set(data.map(d => d.external_holder_name).filter(Boolean)).size;
				summaries.push({
					value: total_count,
					indicator: "Purple",
					label: __("External Assets"),
					datatype: "Int"
				});
				summaries.push({
					value: unique_holders,
					indicator: "Blue",
					label: __("External Partners"),
					datatype: "Int"
				});
			} else {
				// Standard Asset Views (Assets Owned, Assets Held, Assets by Branch, Assets by Department)
				const assigned = data.filter(d => d.status === "Assigned").length;
				const in_store = data.filter(d => d.status === "In Store").length;
				const maintenance = data.filter(d => d.status === "Under Maintenance").length;

				summaries.push({
					value: total_count,
					indicator: "Indigo",
					label: __("Total Assets"),
					datatype: "Int"
				});
				summaries.push({
					value: assigned,
					indicator: "Green",
					label: __("Assigned"),
					datatype: "Int"
				});
				summaries.push({
					value: in_store,
					indicator: "Blue",
					label: __("Available in Store"),
					datatype: "Int"
				});
				summaries.push({
					value: maintenance,
					indicator: "Orange",
					label: __("Under Maintenance"),
					datatype: "Int"
				});
			}

			if (typeof report.render_summary === "function") {
				report.render_summary(summaries);
			}

			// Apply rich thematic classes to each summary-item card
			report.$summary.find(".summary-item").each(function(idx) {
				const $card = $(this);
				const sum = summaries[idx];
				if (sum && sum.indicator) {
					$card.addClass("kpi-" + sum.indicator.toLowerCase());
				}
			});
		}
	},

	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "asset_tag" && value) {
			return `<span style="font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 600; color: #2563eb;">${value}</span>`;
		}

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

		if (column.fieldname === "condition" && data && data.condition) {
			const cond_map = {
				"New": "green",
				"Good": "cyan",
				"Fair": "orange",
				"Poor": "red",
				"Damaged": "red"
			};
			const c = cond_map[data.condition] || "gray";
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
