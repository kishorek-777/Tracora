// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tracora Infra Record", {
	refresh(frm) {
		// Optional one-liner to customize Add Row button label
		frm.fields_dict.field_rows?.grid?.wrapper?.find(".grid-add-row")?.text(__("Add Custom Field"));
	},

	category(frm) {
		// Rule a: Run ONLY when the user changes category field
		// Rule g: Guard against loops
		if (frm._setting_category) {
			return;
		}

		// Rule b: If category is cleared, do nothing. Never wipe rows.
		if (!frm.doc.category) {
			return;
		}

		frm._setting_category = true;

		// Rule c: Load chosen category with frappe.db.get_doc
		frappe.db.get_doc("Tracora Infra Category", frm.doc.category).then((cat) => {
			if (!cat) {
				frm._setting_category = false;
				return;
			}

			// Rule d: Set frm.doc.record_type to category's record_type
			if (cat.record_type) {
				frm.set_value("record_type", cat.record_type);
			}

			// Rule e: Apply template to field_rows
			const existing_rows = frm.doc.field_rows || [];
			const kept_rows = [];
			const kept_labels = new Set();
			let kept_with_values = 0;

			// e.1 & e.2: Remove rows whose field_value is empty; keep every row that has a value
			for (const row of existing_rows) {
				const val = (row.field_value || "").toString().trim();
				if (val) {
					kept_rows.push({
						field_label: (row.field_label || "").trim(),
						field_value: row.field_value
					});
					if (row.field_label) {
						kept_labels.add(row.field_label.trim().toLowerCase());
					}
					kept_with_values++;
				}
			}

			// e.3: For each template label, add a row ONLY if no kept row already has the same label (case-insensitive)
			const template_fields = cat.template_fields || [];
			for (const tf of template_fields) {
				const t_label = (tf.field_label || "").trim();
				if (t_label && !kept_labels.has(t_label.toLowerCase())) {
					kept_rows.push({
						field_label: t_label,
						field_value: ""
					});
					kept_labels.add(t_label.toLowerCase());
				}
			}

			// Rebuild grid rows
			frm.clear_table("field_rows");
			for (const r of kept_rows) {
				const child = frm.add_child("field_rows");
				child.field_label = r.field_label;
				child.field_value = r.field_value;
			}

			// e.4: Refresh grid
			frm.refresh_field("field_rows");

			// Rule f: If any rows with values were kept, show frappe.show_alert
			if (kept_with_values > 0) {
				frappe.show_alert({
					message: __("{0} row(s) with existing values were kept.", [kept_with_values]),
					indicator: "blue"
				});
			}

			frm._setting_category = false;
		}).catch((err) => {
			console.error("Error fetching Tracora Infra Category template:", err);
			frm._setting_category = false;
		});
	}
});
