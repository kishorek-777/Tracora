// Copyright (c) 2026, Tracora and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tracora Settings", {
	refresh(frm) {
		if (frm.doc.hrms_sync_enabled && frappe.user_roles.includes("Tracora Super Admin")) {
			frm.add_custom_button(__("Import Existing HRMS Data"), function() {
				frm.trigger("import_hrms_data");
			}, __("Actions"));
		}
	},

	import_hrms_data(frm) {
		if (!frm.doc.hrms_sync_enabled) {
			frappe.msgprint(__("Please enable HRMS Sync first and save settings."));
			return;
		}

		frappe.confirm(
			__("This will scan HRMS for pre-existing Companies, Branches, Departments, and Employees, and import them into Tracora.<br><br>Do you want to proceed?"),
			function() {
				frappe.call({
					method: "tracora.integrations.hrms.bulk_import",
					args: { dry_run: 0 },
					freeze: true,
					freeze_message: __("Importing HRMS data into Tracora..."),
					callback: function(r) {
						if (r.message) {
							let res = r.message;
							let msg = `
								<h4>${__("HRMS Import Completed")}</h4>
								<ul style="line-height: 1.8;">
									<li><b>${__("Companies Created")}:</b> ${res.created.Company || 0}</li>
									<li><b>${__("Branches Created")}:</b> ${res.created.Branch || 0}</li>
									<li><b>${__("Departments Created")}:</b> ${res.created.Department || 0}</li>
									<li><b>${__("Employees Created")}:</b> ${res.created.Employee || 0}</li>
									<li><b>${__("Employees Updated")}:</b> ${res.updated.Employee || 0}</li>
								</ul>
							`;
							if (res.conflicts && res.conflicts.length > 0) {
								msg += `<p class="text-warning">${__("Some records had conflicts. Please check Tracora Sync Conflict.")}</p>`;
							}
							frappe.msgprint({
								title: __("Import Results"),
								message: msg,
								indicator: "green"
							});
							frm.reload_doc();
						}
					}
				});
			}
		);
	}
});
