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
			rewritten.push(f.slice ? f.slice() : f);
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
			rewritten.push({ ...f });
		} else {
			rewritten.push(f);
		}
	}
	return rewritten;
}

function update_search_box_label_and_placeholder(listview) {
	const control = listview.page?.fields_dict?.title;
	if (!control) {
		return;
	}

	// 1. Update control's definition properties
	if (control.df) {
		control.df.label = __("Search");
		control.df.placeholder = __("Search any field");
	}

	// 2. Invoke control's setter methods if available
	if (typeof control.set_label === "function") {
		control.set_label(__("Search"));
	}
	if (typeof control.set_placeholder === "function") {
		control.set_placeholder(__("Search any field"));
	}
	if (typeof control.refresh === "function") {
		control.refresh();
	}

	// 3. Directly update input element placeholder
	if (control.$input) {
		control.$input.attr("placeholder", __("Search any field"));
	}

	// 4. Update wrapper title / tooltip if present
	if (control.wrapper) {
		$(control.wrapper).attr("title", __("Search"));
	}
}

function clean_leaked_filter(listview) {
	if (!listview || !listview.filter_area) {
		return;
	}

	const filters = listview.filter_area.get() || [];
	const has_leaked = filters.some((f) => {
		if (Array.isArray(f)) {
			return f[1] === "name" && f[3] === "__select_record_type__";
		} else if (f && typeof f === "object") {
			return f.fieldname === "name" && f.value === "__select_record_type__";
		}
		return false;
	});

	if (has_leaked) {
		listview.filter_area.remove("name");
	}

	const name_control = listview.page?.fields_dict?.name;
	if (name_control && typeof name_control.get_value === "function") {
		if (name_control.get_value() === "__select_record_type__") {
			name_control.set_value("");
		}
	}

	if (window.location.search && window.location.search.includes("__select_record_type__")) {
		try {
			const url = new URL(window.location.href);
			url.searchParams.delete("name");
			for (const [key, value] of Array.from(url.searchParams.entries())) {
				if (value === "__select_record_type__") {
					url.searchParams.delete(key);
				}
			}
			const search = url.searchParams.toString();
			const clean_url = url.pathname + (search ? "?" + search : "") + url.hash;
			window.history.replaceState(null, null, clean_url);
		} catch (e) {
			const clean_url = window.location.href
				.replace(/[?&]name=__select_record_type__/, "")
				.replace(/\?$/, "");
			window.history.replaceState(null, null, clean_url);
		}
	}
}

frappe.listview_settings["Tracora Infra Record"] = {
	onload(listview) {
		// Clean up any leaked impossible filter from previous sessions
		clean_leaked_filter(listview);

		// Relabel Title filter box to Search and set placeholder to "Search any field"
		update_search_box_label_and_placeholder(listview);

		// Wrap get_args to mark call as server rows request
		const standard_get_args = listview.get_args.bind(listview);
		listview.get_args = function () {
			listview._for_server_request = true;
			try {
				const args = standard_get_args();
				args.filters = rewrite_filters_for_request(args.filters);
				if (!has_record_type_selected(listview)) {
					args.filters = args.filters || [];
					const has_impossible_filter = args.filters.some(
						(f) => Array.isArray(f) && f[1] === "name" && f[3] === "__select_record_type__"
					);
					if (!has_impossible_filter) {
						args.filters = args.filters.concat([
							["Tracora Infra Record", "name", "=", "__select_record_type__"],
						]);
					}
				}
				return args;
			} finally {
				listview._for_server_request = false;
			}
		};

		// Wrap get_count_str to mark call as server count request
		if (listview.get_count_str) {
			const standard_get_count_str = listview.get_count_str.bind(listview);
			listview.get_count_str = function () {
				listview._for_server_request = true;
				try {
					return standard_get_count_str();
				} finally {
					listview._for_server_request = false;
				}
			};
		}

		// Wrap get_filters_for_args so server requests get rewritten filters & impossible filter,
		// while URL building, user settings, and other callers get untouched filters.
		if (listview.get_filters_for_args) {
			const standard_get_filters_for_args = listview.get_filters_for_args.bind(listview);
			listview.get_filters_for_args = function () {
				const filters = standard_get_filters_for_args();
				if (!listview._for_server_request) {
					return filters;
				}

				let request_filters = rewrite_filters_for_request(filters);
				if (!has_record_type_selected(listview)) {
					request_filters = request_filters || [];
					const has_impossible_filter = request_filters.some(
						(f) => Array.isArray(f) && f[1] === "name" && f[3] === "__select_record_type__"
					);
					if (!has_impossible_filter) {
						request_filters = request_filters.concat([
							["Tracora Infra Record", "name", "=", "__select_record_type__"],
						]);
					}
				}
				return request_filters;
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
		clean_leaked_filter(listview);
		update_search_box_label_and_placeholder(listview);
	},
};
