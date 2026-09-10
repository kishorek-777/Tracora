// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.listview_settings['Tracora Asset'] = {
	add_fields: ['status', 'brand', 'holding_company', 'location', 'assigned_to', 'is_shared', 'condition', 'label_printed_on'],
	get_indicator: function(doc) {
		const colors = {
			'In Store': 'blue',
			'Assigned': 'green',
			'Under Maintenance': 'orange',
			'Damaged': 'orange',
			'Lost': 'red',
			'Recovered': 'yellow',
			'Released': 'grey',
			'Retired': 'grey'
		};
		return [__(doc.status), colors[doc.status] || 'grey', 'status,=,' + doc.status];
	},
	onload: function(listview) {
		listview.page.empty_state_text = __('No assets yet. Register the first one.');

		// Batch printing UI per P7 & FR-47: select rows -> Print labels
		listview.page.add_actions_menu_item(__('Print Labels'), function() {
			const selected = listview.get_checked_items();
			if (!selected || !selected.length) {
				frappe.msgprint(__('Please select at least one asset to print labels.'));
				return;
			}
			const asset_names = selected.map(item => item.name);
			const count = asset_names.length;
			const first_asset = asset_names[0];

			// Read-only preview of the first label (does NOT write movements or mutate DB)
			frappe.call({
				method: 'tracora.api.labels.get_label_preview',
				args: { asset: first_asset },
				freeze: true,
				freeze_message: __('Loading label preview...'),
				callback: function(r) {
					if (!r.message) return;
					const preview = r.message;

					const preview_dialog = new frappe.ui.Dialog({
						title: __('Print Labels ({0} selected)', [count]),
						fields: [
							{
								fieldname: 'preview_html',
								fieldtype: 'HTML'
							}
						],
						primary_action_label: count === 1 ? __('Print 1 Label') : __('Print {0} Labels', [count]),
						primary_action: function() {
							preview_dialog.get_primary_btn().prop('disabled', true);
							frappe.call({
								method: 'tracora.api.labels.print_labels',
								args: { assets: asset_names },
								freeze: true,
								freeze_message: __('Preparing {0} label(s)...', [count]),
								callback: function(res) {
									preview_dialog.hide();
									if (res.message && res.message.html) {
										const print_win = window.open('', '_blank');
										if (print_win) {
											print_win.document.open();
											print_win.document.write(res.message.html);
											print_win.document.close();
											print_win.focus();
											setTimeout(() => {
												print_win.print();
											}, 350);
										} else {
											frappe.msgprint(__('Please allow popups to print labels.'));
										}
										listview.refresh();
									}
								},
								always: function() {
									preview_dialog.get_primary_btn().prop('disabled', false);
								}
							});
						}
					});

					const preview_desc = count === 1
						? __('Printing 1 asset label.')
						: __('Printing {0} asset labels in a single document.', [count]);

					const preview_card = `
						<div class="mb-3 text-muted" style="font-size: 13px;">
							${preview_desc}
						</div>
						<div class="p-2 mb-2" style="background: #f8f9fa; border: 1px dashed #cbd5e0; border-radius: 4px; display: inline-block;">
							<div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #718096; margin-bottom: 6px;">
								${__('Preview (First Label: {0})', [frappe.utils.escape_html(preview.asset_tag)])}
							</div>
							<div style="border: 1px solid #1a202c; border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); background: #ffffff;">
								${preview.preview_html}
							</div>
						</div>
					`;
					preview_dialog.fields_dict.preview_html.$wrapper.html(preview_card);
					preview_dialog.show();
				}
			});
		});
	}
};
