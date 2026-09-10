// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.listview_settings["Tracora Sync Conflict"] = {
	get_indicator: function(doc) {
		if (doc.conflict_status === "Open") {
			return [__("Open"), "orange", "conflict_status,=,Open"];
		} else if (doc.conflict_status === "Resolved") {
			return [__("Resolved"), "green", "conflict_status,=,Resolved"];
		}
	},
	onload: function(listview) {
		if (!listview.filter_area.get().some(f => f[1] === "conflict_status")) {
			listview.filter_area.add([["Tracora Sync Conflict", "conflict_status", "=", "Open"]]);
		}
	}
};
