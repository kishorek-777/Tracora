frappe.listview_settings['Tracora Employee'] = {
	get_indicator: function(doc) {
		if (doc.status === 'Active') {
			return [__("Active"), "green", "status,=,Active"];
		} else if (doc.status === 'Pending Clearance') {
			return [__("Pending Clearance"), "orange", "status,=,Pending Clearance"];
		} else if (doc.status === 'Exited') {
			return [__("Exited"), "gray", "status,=,Exited"];
		}
	}
};
