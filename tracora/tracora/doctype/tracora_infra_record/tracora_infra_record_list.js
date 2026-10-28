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

function escape_like_term(word) {
	return word
		.replace(/\\/g, "\\\\")
		.replace(/%/g, "\\%")
		.replace(/_/g, "\\_");
}

function rewrite_filters_for_request(filters) {
	if (!filters || !Array.isArray(filters)) {
		return filters;
	}

	const rewritten = [];
	for (const f of filters) {
		if (Array.isArray(f)) {
			const doctype = f[0];
			const fieldname = f[1];
			const operator = (f[2] || "").toString().toLowerCase();
			const value = f[3];

			if (fieldname === "title" && operator === "like") {
				let text = String(value || "");
				if (text.startsWith("%") && text.endsWith("%") && text.length >= 2) {
					text = text.slice(1, -1);
				}
				const words = text.trim().split(/\s+/).filter(Boolean);
				for (const word of words) {
					const escaped = escape_like_term(word);
					rewritten.push([
						doctype || "Tracora Infra Record",
						"search_text",
						"like",
						"%" + escaped + "%",
					]);
				}
				continue;
			}
			rewritten.push(f);
		} else if (f && typeof f === "object") {
			const fieldname = f.fieldname;
			const operator = (f.operator || f.condition || "").toString().toLowerCase();
			const value = f.value;

			if (fieldname === "title" && operator === "like") {
				let text = String(value || "");
				if (text.startsWith("%") && text.endsWith("%") && text.length >= 2) {
					text = text.slice(1, -1);
				}
				const words = text.trim().split(/\s+/).filter(Boolean);
				for (const word of words) {
					const escaped = escape_like_term(word);
					rewritten.push({
						...f,
						fieldname: "search_text",
						operator: "like",
						condition: "like",
						value: "%" + escaped + "%",
					});
				}
				continue;
			}
			rewritten.push(f);
		} else {
			rewritten.push(f);
		}
	}
	return rewritten;
}

frappe.listview_settings["Tracora Infra Record"] = {
	onload(listview) {
		// Cosmetic relabeling of Title filter to Search via documented set_label API
		if (listview.page?.fields_dict?.title?.set_label) {
			listview.page.fields_dict.title.set_label(__("Search"));
		}

		// Wrap get_args to rewrite title like filters and enforce record_type selection
		const standard_get_args = listview.get_args.bind(listview);
		listview.get_args = function () {
			const args = standard_get_args();
			args.filters = rewrite_filters_for_request(args.filters);
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

		// Wrap get_filters_for_args so count query also reflects rewritten filters & 0 rows rule
		if (listview.get_filters_for_args) {
			const standard_get_filters_for_args = listview.get_filters_for_args.bind(listview);
			listview.get_filters_for_args = function () {
				let filters = standard_get_filters_for_args();
				filters = rewrite_filters_for_request(filters);
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
					<p>${__("Select a Record Type to view records.")}</p>
				</div>`;
			}
			return standard_get_no_result_message();
		};
	},

	refresh(listview) {
		if (listview.page?.fields_dict?.title?.set_label) {
			listview.page.fields_dict.title.set_label(__("Search"));
		}
	},
};
