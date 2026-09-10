// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.listview_settings['Tracora Asset Movement'] = {
	hide_name_column: false,
	add_fields: ["asset", "movement_type", "from_employee", "to_employee", "from_location", "to_location", "from_status", "to_status", "movement_date", "remarks"],
	get_indicator: function(doc) {
		const colors = {
			"Assign": "green",
			"Unassign": "orange",
			"Location Change": "blue",
			"Custody Transfer": "cyan",
			"Ownership Transfer": "purple",
			"Status Change": "yellow",
			"Condition Change": "yellow",
			"Maintenance Sent": "orange",
			"Maintenance Returned": "green",
			"Beyond Repair": "red",
			"Exit Release": "gray",
			"Recovered": "green",
			"Released": "gray",
			"Label Reprint": "blue"
		};
		return [__(doc.movement_type), colors[doc.movement_type] || "gray", "movement_type,=," + doc.movement_type];
	},
	formatters: {
		movement_type: function(val, df, doc) {
			let sentence = `<b>${doc.movement_type}</b>`;
			if (doc.movement_type === "Assign" && doc.to_employee) {
				sentence += ` to ${doc.to_employee}`;
			} else if (doc.movement_type === "Unassign" && doc.from_employee) {
				sentence += ` from ${doc.from_employee}`;
			} else if (doc.movement_type === "Custody Transfer") {
				sentence += ` ${doc.from_employee || 'Unassigned'} → ${doc.to_employee || 'Unassigned'}`;
			} else if (doc.movement_type === "Location Change") {
				sentence += ` ${doc.from_location || 'None'} → ${doc.to_location || 'None'}`;
			} else if (doc.to_status) {
				sentence += ` (${doc.from_status || 'None'} → ${doc.to_status})`;
			}
			return sentence;
		}
	}
};
