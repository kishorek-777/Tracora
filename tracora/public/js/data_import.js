frappe.ui.form.on("Data Import", {
	setup(frm) {
		const roles = frappe.user_roles || [];
		const is_restricted =
			frappe.session.user !== "Administrator" &&
			!roles.includes("System Manager") &&
			(roles.includes("Tracora Admin") || roles.includes("Tracora Super Admin"));

		if (is_restricted) {
			frm.set_query("reference_doctype", () => {
				return {
					filters: {
						module: "Tracora",
						allow_import: 1,
						istable: 0,
						issingle: 0,
						custom: 0,
						name: ["in", ["Tracora Asset", "Tracora Software Licence"]],
					},
				};
			});
		}
	},
});
