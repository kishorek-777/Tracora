// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

function has_record_type_selected(listview) {
	if (!listview || !listview.filter_area) {
		return false;
	}

	const filters = listview.filter_area.get() || [];
	return filters.some((f) => {
		if (Array.isArray(f)) {
			// Format: [doctype, fieldname, operator, value, hidden]
			return (
				f[1] === "record_type" &&
				f[2] === "=" &&
				f[3] !== undefined &&
				f[3] !== null &&
				String(f[3]).trim() !== ""
			);
		} else if (f && typeof f === "object") {
			return (
				f.fieldname === "record_type" &&
				(f.operator === "=" || f.condition === "=") &&
				f.value !== undefined &&
				f.value !== null &&
				String(f.value).trim() !== ""
			);
		}
		return false;
	});
}

frappe.listview_settings["Tracora Infra Record"] = {
	onload(listview) {
		// Wrap get_args to enforce zero rows when no Record Type is selected
		const standard_get_args = listview.get_args.bind(listview);
		listview.get_args = function () {
			const args = standard_get_args();
			if (!has_record_type_selected(listview)) {
				args.filters = args.filters || [];
				const has_impossible_filter = args.filters.some(
					(f) => Array.isArray(f) && f[1] === "name" && f[3] === "__select_record_type__"
				);
				if (!has_impossible_filter) {
					args.filters.push(["Tracora Infra Record", "name", "=", "__select_record_type__"]);
				}
			}
			return args;
		};

		// Wrap get_filters_for_args so count query also reflects 0 rows
		if (listview.get_filters_for_args) {
			const standard_get_filters_for_args = listview.get_filters_for_args.bind(listview);
			listview.get_filters_for_args = function () {
				const filters = standard_get_filters_for_args();
				if (!has_record_type_selected(listview)) {
					const has_impossible_filter = filters.some(
						(f) => Array.isArray(f) && f[1] === "name" && f[3] === "__select_record_type__"
					);
					if (!has_impossible_filter) {
						filters.push(["Tracora Infra Record", "name", "=", "__select_record_type__"]);
					}
				}
				return filters;
			};
		}

		// Wrap get_no_result_message to show custom empty state when no type is selected
		const standard_get_no_result_message = listview.get_no_result_message.bind(listview);
		listview.get_no_result_message = function () {
			if (!has_record_type_selected(listview)) {
				return `<div class="msg-box no-border">
					<div class="mb-4">
						<svg class="icon icon-xl" style="stroke: var(--text-light);">
							<use href="#icon-small-file"></use>
						</svg>
					</div>
					<p>${__("Select a Record Type (Device, Building, Vendor or Other) to view records.")}</p>
				</div>`;
			}
			return standard_get_no_result_message();
		};
	},
};
