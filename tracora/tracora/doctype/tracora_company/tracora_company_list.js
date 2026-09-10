frappe.listview_settings['Tracora Company'] = {
	get_indicator: function(doc) {
		if (doc.company_type === 'Internal') {
			return [__("Internal"), "green", "company_type,=,Internal"];
		} else if (doc.company_type === 'External') {
			return [__("External"), "blue", "company_type,=,External"];
		}
	}
};
