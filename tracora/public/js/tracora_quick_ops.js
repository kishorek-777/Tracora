// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.provide('tracora');

tracora.open_quick_ops = function(initial_tag) {
	let selected_asset = null;

	const d = new frappe.ui.Dialog({
		title: __('⚡ Quick Asset Operations'),
		fields: [
			{
				label: __('Asset Tag / Serial / Barcode'),
				fieldname: 'scan_input',
				fieldtype: 'Data',
				reqd: 0,
				description: __('Scan with barcode reader or type tag and press Enter.')
			},
			{
				fieldtype: 'HTML',
				fieldname: 'asset_preview_html'
			}
		],
		primary_action_label: __('Lookup Asset'),
		primary_action: function(values) {
			const tag = (values.scan_input || '').trim();
			if (!tag) {
				frappe.msgprint(__('Please scan or enter an asset tag.'));
				return;
			}
			lookup_asset(tag);
		}
	});

	function lookup_asset(query_str) {
		const preview_container = d.fields_dict.asset_preview_html.$wrapper;
		preview_container.html(`
			<div class="text-center p-4 text-muted">
				<div class="spinner-border spinner-border-sm mr-2" role="status"></div>
				${__('Locating hardware record...')}
			</div>
		`);

		// Try finding asset by asset_tag, serial_no, or name
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Tracora Asset',
				filters: [
					['Tracora Asset', 'asset_tag', '=', query_str]
				],
				fields: ['name', 'asset_tag', 'asset_name', 'brand', 'model_number', 'serial_no', 'status', 'assigned_to', 'holding_company', 'location', 'condition'],
				limit: 1
			},
			callback: function(r) {
				let asset = (r.message && r.message.length) ? r.message[0] : null;

				if (!asset) {
					// Fallback search by serial_no or doc name
					frappe.call({
						method: 'frappe.client.get_list',
						args: {
							doctype: 'Tracora Asset',
							filters: [
								['Tracora Asset', 'name', '=', query_str]
							],
							fields: ['name', 'asset_tag', 'asset_name', 'brand', 'model_number', 'serial_no', 'status', 'assigned_to', 'holding_company', 'location', 'condition'],
							limit: 1
						},
						callback: function(r2) {
							asset = (r2.message && r2.message.length) ? r2.message[0] : null;
							if (!asset) {
								render_not_found(query_str);
							} else {
								render_asset_card(asset);
							}
						}
					});
				} else {
					render_asset_card(asset);
				}
			}
		});
	}

	function render_not_found(query_str) {
		selected_asset = null;
		const preview_container = d.fields_dict.asset_preview_html.$wrapper;
		preview_container.html(`
			<div class="alert alert-warning my-3" style="font-size: 13px;">
				<strong>⚠️ ${__('Asset Not Found:')}</strong> ${__('No hardware record matches "{0}". Check spelling or register a new asset.', [frappe.utils.escape_html(query_str)])}
			</div>
		`);
	}

	function render_asset_card(asset) {
		selected_asset = asset;
		const preview_container = d.fields_dict.asset_preview_html.$wrapper;

		const status_colors = {
			'In Store': 'blue',
			'Assigned': 'green',
			'Under Maintenance': 'orange',
			'Damaged': 'red',
			'Lost': 'red',
			'Recovered': 'yellow'
		};
		const status_pill = `<span class="indicator-pill ${status_colors[asset.status] || 'gray'}">${asset.status}</span>`;
		const holder_str = asset.assigned_to
			? `<div class="tracora-avatar-pill mt-1"><span class="tracora-avatar-circle">${frappe.utils.escape_html((asset.assigned_to[0] || 'A').toUpperCase())}</span><span>${frappe.utils.escape_html(asset.assigned_to)}</span></div>`
			: `<span class="text-muted" style="font-size: 12px;">${__('In Store (Unassigned)')}</span>`;

		const actions_html = `
			<div class="d-flex flex-wrap gap-2 mt-3 pt-3" style="border-top: 1px solid #e2e8f0;">
				${asset.status === 'In Store' ? `
					<button class="btn btn-sm btn-primary" id="btn-quick-handover">
						➕ ${__('Handover to Employee')}
					</button>
				` : ''}

				${asset.status === 'Assigned' ? `
					<button class="btn btn-sm btn-info" id="btn-quick-return">
						↩️ ${__('Return to Stock')}
					</button>
				` : ''}

				<button class="btn btn-sm btn-success" id="btn-quick-audit">
					✅ ${__('Mark Physical Audit OK')}
				</button>

				<button class="btn btn-sm btn-secondary" id="btn-open-form">
					📄 ${__('Open Full Record')}
				</button>
			</div>
		`;

		preview_container.html(`
			<div class="tracora-asset-card-found">
				<div class="d-flex justify-content-between align-items-start">
					<div>
						<div class="d-flex align-items-center gap-2 mb-1">
							<span class="tracora-tag-pill">${frappe.utils.escape_html(asset.asset_tag || asset.name)}</span>
							${status_pill}
						</div>
						<div style="font-size: 15px; font-weight: 700; color: #0f172a;">
							${frappe.utils.escape_html(asset.brand || '')} ${frappe.utils.escape_html(asset.model_number || asset.asset_name || '')}
						</div>
						<div class="text-muted mt-1" style="font-size: 11px;">
							Serial: <code>${frappe.utils.escape_html(asset.serial_no || '-')}</code> &bull; Location: 📍 <b>${frappe.utils.escape_html(asset.location || 'HQ')}</b>
						</div>
					</div>
					<div class="text-right">
						<span class="text-muted" style="font-size: 11px; text-transform: uppercase; font-weight: 600;">${__('Current Custody')}</span>
						${holder_str}
					</div>
				</div>

				${actions_html}
			</div>
		`);

		// Bind actions
		$('#btn-open-form').on('click', function() {
			d.hide();
			frappe.set_route('Form', 'Tracora Asset', asset.name);
		});

		$('#btn-quick-audit').on('click', function() {
			frappe.call({
				method: 'tracora.api.audit.submit_asset_audit',
				args: {
					asset: asset.name,
					audit_status: 'Verified',
					condition: asset.condition || 'Good',
					remarks: 'Quick Barcode Scan Verification',
					location: asset.location
				},
				freeze: true,
				freeze_message: __('Recording verification...'),
				callback: function(res) {
					if (res.message && res.message.success) {
						frappe.show_alert({
							message: __('Physical verification recorded for {0}', [asset.asset_tag || asset.name]),
							indicator: 'green'
						});
						d.hide();
					}
				}
			});
		});

		$('#btn-quick-handover').on('click', function() {
			const assign_diag = new frappe.ui.Dialog({
				title: __('Handover Asset: {0}', [asset.asset_tag || asset.name]),
				fields: [
					{
						label: __('Employee'),
						fieldname: 'employee',
						fieldtype: 'Link',
						options: 'Tracora Employee',
						reqd: 1
					},
					{
						label: __('Remarks'),
						fieldname: 'remarks',
						fieldtype: 'Small Text',
						default: 'Quick scan assignment'
					}
				],
				primary_action_label: __('Confirm Handover'),
				primary_action: function(vals) {
					assign_diag.hide();
					frappe.call({
						method: 'tracora.api.assign.assign_single',
						args: {
							asset: asset.name,
							employee: vals.employee,
							remarks: vals.remarks
						},
						freeze: true,
						freeze_message: __('Assigning custody...'),
						callback: function(r) {
							if (r.message && r.message.success) {
								frappe.show_alert({
									message: __('Custody assigned to {0}', [vals.employee]),
									indicator: 'green'
								});
								d.hide();
								if (cur_list) cur_list.refresh();
							}
						}
					});
				}
			});
			assign_diag.show();
		});

		$('#btn-quick-return').on('click', function() {
			const return_diag = new frappe.ui.Dialog({
				title: __('Return Asset to Stock: {0}', [asset.asset_tag || asset.name]),
				fields: [
					{
						label: __('Return Condition'),
						fieldname: 'condition',
						fieldtype: 'Select',
						options: ['Good', 'Fair', 'Poor', 'Damaged', 'Not Working'],
						default: 'Good',
						reqd: 1
					},
					{
						label: __('Remarks'),
						fieldname: 'remarks',
						fieldtype: 'Small Text',
						reqd: 1,
						default: 'Returned via quick scanner'
					}
				],
				primary_action_label: __('Confirm Check-In'),
				primary_action: function(vals) {
					return_diag.hide();
					frappe.call({
						method: 'tracora.api.assign.unassign_single',
						args: {
							asset: asset.name,
							remarks: vals.remarks,
							condition_on_unassign: vals.condition
						},
						freeze: true,
						freeze_message: __('Returning asset to stock...'),
						callback: function(r) {
							if (r.message && r.message.success) {
								frappe.show_alert({
									message: __('Asset {0} returned to stock successfully', [asset.asset_tag || asset.name]),
									indicator: 'green'
								});
								d.hide();
								if (cur_list) cur_list.refresh();
							}
						}
					});
				}
			});
			return_diag.show();
		});
	}

	d.show();

	// Focus input immediately and handle Enter key for physical laser scanners
	setTimeout(() => {
		const $inp = d.fields_dict.scan_input.$input;
		$inp.focus();
		$inp.on('keydown', function(e) {
			if (e.which === 13) {
				e.preventDefault();
				const val = ($inp.val() || '').trim();
				if (val) {
					lookup_asset(val);
				}
			}
		});

		if (initial_tag) {
			$inp.val(initial_tag);
			lookup_asset(initial_tag);
		}
	}, 150);
};

// Global Keyboard Shortcut: Ctrl + Shift + S triggers Quick Operations
$(document).on('keydown', function(e) {
	if (e.ctrlKey && e.shiftKey && (e.key === 'S' || e.key === 's')) {
		e.preventDefault();
		tracora.open_quick_ops();
	}
});

