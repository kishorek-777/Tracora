// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tracora Maintenance Log", {
	refresh(frm) {
		if (frm.doc.log_status === "Open") {
			frm.add_custom_button(__("Close Maintenance"), () => {
				const d = new frappe.ui.Dialog({
					title: __("Close Maintenance Log"),
					fields: [
						{
							fieldname: "condition_on_return",
							fieldtype: "Select",
							label: __("Condition on Return"),
							options: "\nNew\nGood\nFair\nPoor\nNot Working",
							reqd: 1,
						},
						{
							fieldname: "date_returned",
							fieldtype: "Date",
							label: __("Date Returned"),
							default: frappe.datetime.get_today(),
							reqd: 1,
						},
						{
							fieldname: "is_beyond_repair",
							fieldtype: "Check",
							label: __("Beyond Repair (Retire Asset)"),
						},
						{
							fieldname: "remarks",
							fieldtype: "Small Text",
							label: __("Closing Remarks"),
						},
					],
					primary_action_label: __("Confirm Close"),
					primary_action(values) {
						frappe.call({
							method: "tracora.api.maintenance.close_maintenance",
							args: {
								log_name: frm.doc.name,
								condition_on_return: values.condition_on_return,
								date_returned: values.date_returned,
								is_beyond_repair: values.is_beyond_repair,
								remarks: values.remarks,
							},
							freeze: true,
							freeze_message: __("Closing maintenance log..."),
							callback(r) {
								if (!r.exc) {
									d.hide();
									frm.reload_doc();
								}
							},
						});
					},
				});
				d.show();
			}).addClass("btn-primary");
		}
	},
});

// List View Indicator with Overdue Calculation
frappe.listview_settings["Tracora Maintenance Log"] = {
	add_fields: ["due_date", "log_status"],
	get_indicator(doc) {
		if (doc.log_status === "Open") {
			// Precedence Rule: Red (Overdue) takes precedence over Orange (Open) when due_date < today
			if (doc.due_date && frappe.datetime.get_diff(doc.due_date, frappe.datetime.get_today()) < 0) {
				return [__("Overdue"), "red", "due_date,<,today|log_status,=,Open"];
			}
			return [__("Open"), "orange", "log_status,=,Open"];
		} else if (doc.log_status === "Closed") {
			return [__("Closed"), "green", "log_status,=,Closed"];
		} else if (doc.log_status === "Beyond Repair") {
			return [__("Beyond Repair"), "gray", "log_status,=,Beyond Repair"];
		}
	},
	onload(listview) {
		// Work queue default: show Open logs
		if (!listview.filter_area.get().some((f) => f[1] === "log_status")) {
			listview.filter_area.add([[listview.doctype, "log_status", "=", "Open"]]);
		}
	},
};