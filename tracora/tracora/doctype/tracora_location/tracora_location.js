frappe.ui.form.on('Tracora Location', {
	refresh: function(frm) {
		if (frm.doc.latitude != null && frm.doc.longitude != null) {
			frm.add_custom_button(__('Open in Maps'), function() {
				const url = `https://www.google.com/maps?q=${frm.doc.latitude},${frm.doc.longitude}`;
				window.open(url, '_blank');
			});
		}
	}
});
