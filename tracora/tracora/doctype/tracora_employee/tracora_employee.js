// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tracora Employee', {
	setup: function(frm) {
		frm.set_query('branch', function() {
			return {
				filters: {
					company: frm.doc.company || ''
				}
			};
		});
		frm.set_query('department', function() {
			return {
				filters: {
					company: frm.doc.company || ''
				}
			};
		});
	},

	onload: function(frm) {
		if (frm.doc.source === 'HRMS') {
			const hrms_owned_fields = [
				'employee_name',
				'mobile',
				'email',
				'date_of_birth',
				'company',
				'branch',
				'department',
				'status',
				'permanent_address'
			];
			hrms_owned_fields.forEach(f => {
				frm.set_df_property(f, 'read_only', 1);
			});
		}
	},

	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.events.render_assets_held_section(frm);
		}
	},

	company: function(frm) {
		if (frm.doc.company) {
			frappe.db.get_value('Tracora Company', frm.doc.company, 'company_type').then(r => {
				if (r && r.message) {
					frm.set_value('company_type', r.message.company_type);
					frm.refresh_fields();
				}
			});
		} else {
			frm.set_value('company_type', '');
			frm.refresh_fields();
		}
	},

	render_assets_held_section: function(frm) {
		frappe.call({
			method: 'tracora.api.assign.get_employee_held_assets',
			args: { employee: frm.doc.name },
			callback: function(r) {
				const assets = r.message || [];
				let content_html = '';

				if (assets.length === 0) {
					content_html = `
						<div class="text-center py-4 my-2 border rounded" style="background: var(--card-bg, #f7fafc);">
							<p class="text-muted mb-2">${__('No assets assigned.')}</p>
							<button class="btn btn-sm btn-primary" id="btn-assign-assets-empty">${__('Assign Assets')}</button>
						</div>
					`;
				} else {
					let rows = assets.map(a => `
						<tr>
							<td><a href="/app/tracora-asset/${encodeURIComponent(a.name)}" class="font-weight-bold">${frappe.utils.escape_html(a.asset_tag || a.name)}</a></td>
							<td>${frappe.utils.escape_html(a.asset_name || '-')}</td>
							<td>${frappe.utils.escape_html(a.brand || '-')} ${a.model_number ? `(${frappe.utils.escape_html(a.model_number)})` : ''}</td>
							<td>${frappe.utils.escape_html(a.serial_no || '-')}</td>
							<td>${a.assigned_on ? frappe.datetime.str_to_user(a.assigned_on) : '-'}</td>
							<td>${frappe.utils.escape_html(a.location || '-')}</td>
							<td><span class="badge badge-success">${frappe.utils.escape_html(a.status || 'Assigned')}</span></td>
						</tr>
					`).join('');

					content_html = `
						<div class="my-2 border rounded p-3" style="background: var(--card-bg, #f7fafc);">
							<div class="d-flex justify-content-between align-items-center mb-3">
								<h6 class="text-muted uppercase mb-0" style="font-size: 12px; font-weight: 600;">${__('Assets Held')} (${assets.length})</h6>
								<button class="btn btn-sm btn-primary" id="btn-assign-more-assets">${__('Assign Assets')}</button>
							</div>
							<div class="table-responsive">
								<table class="table table-sm table-hover mb-0">
									<thead class="text-muted small">
										<tr>
											<th>${__('Asset Tag')}</th>
											<th>${__('Asset Name')}</th>
											<th>${__('Brand / Model')}</th>
											<th>${__('Serial Number')}</th>
											<th>${__('Assigned On')}</th>
											<th>${__('Location')}</th>
											<th>${__('Status')}</th>
										</tr>
									</thead>
									<tbody>
										${rows}
									</tbody>
								</table>
							</div>
						</div>
					`;
				}

				if (!frm.assets_held_wrapper) {
					frm.assets_held_wrapper = $('<div class="tracora-assets-held-container my-3"></div>');
					frm.dashboard.wrapper.append(frm.assets_held_wrapper);
				}
				frm.assets_held_wrapper.html(content_html);

				// Bind button clicks
				frm.assets_held_wrapper.find('#btn-assign-assets-empty, #btn-assign-more-assets').on('click', function(e) {
					e.preventDefault();
					frm.events.show_batch_assign_modal(frm);
				});
			}
		});
	},

	show_batch_assign_modal: function(frm) {
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Tracora Asset',
				filters: {
					status: 'In Store',
					is_shared: 0
				},
				fields: ['name', 'asset_tag', 'asset_name', 'brand', 'model_number', 'serial_no', 'location'],
				limit_page_length: 100
			},
			callback: function(r) {
				const available_assets = r.message || [];
				if (available_assets.length === 0) {
					frappe.msgprint({
						title: __('No Available Assets'),
						message: __('There are no hardware assets currently In Store available for assignment.'),
						indicator: 'orange'
					});
					return;
				}

				let table_rows = available_assets.map(a => `
					<tr>
						<td style="width: 30px; text-align: center;">
							<input type="checkbox" class="asset-checkbox" data-asset-name="${frappe.utils.escape_html(a.name)}" />
						</td>
						<td><strong>${frappe.utils.escape_html(a.asset_tag || a.name)}</strong></td>
						<td>${frappe.utils.escape_html(a.asset_name || '-')}</td>
						<td>${frappe.utils.escape_html(a.brand || '-')} ${a.model_number ? `(${frappe.utils.escape_html(a.model_number)})` : ''}</td>
						<td>${frappe.utils.escape_html(a.serial_no || '-')}</td>
						<td>${frappe.utils.escape_html(a.location || '-')}</td>
					</tr>
				`).join('');

				const d = new frappe.ui.Dialog({
					title: __('Assign Assets to {0}', [frm.doc.employee_name || frm.doc.name]),
					size: 'large',
					fields: [
						{
							fieldname: 'assignment_date',
							fieldtype: 'Date',
							label: __('Assignment Date'),
							default: frappe.datetime.nowdate(),
							reqd: 1
						},
						{
							fieldname: 'reference',
							fieldtype: 'Data',
							label: __('Reference / Request ID')
						},
						{
							fieldname: 'asset_picker_html',
							fieldtype: 'HTML',
							options: `
								<div class="mb-2 d-flex justify-content-between align-items-center">
									<span class="text-muted small">${__('Select available assets to assign:')}</span>
									<button type="button" class="btn btn-xs btn-default" id="btn-select-all-assets">${__('Select All')}</button>
								</div>
								<div style="max-height: 280px; overflow-y: auto; border: 1px solid var(--border-color, #d1d5db); border-radius: 4px;">
									<table class="table table-sm table-striped mb-0">
										<thead class="small text-muted" style="position: sticky; top: 0; background: var(--card-bg, #f7fafc);">
											<tr>
												<th></th>
												<th>${__('Tag')}</th>
												<th>${__('Name')}</th>
												<th>${__('Brand')}</th>
												<th>${__('Serial')}</th>
												<th>${__('Location')}</th>
											</tr>
										</thead>
										<tbody>
											${table_rows}
										</tbody>
									</table>
								</div>
							`
						}
					],
					primary_action_label: __('Assign Selected Assets'),
					primary_action: function(values) {
						const selected = [];
						d.$wrapper.find('.asset-checkbox:checked').each(function() {
							selected.push($(this).data('asset-name'));
						});

						if (selected.length === 0) {
							frappe.msgprint(__('Please select at least one asset to assign.'));
							return;
						}

						d.get_primary_btn().prop('disabled', true);
						frappe.call({
							method: 'tracora.api.assign.assign_to_employee',
							args: {
								employee: frm.doc.name,
								assets: selected,
								reference: values.reference,
								assignment_date: values.assignment_date
							},
							freeze: true,
							freeze_message: __('Assigning {0} Assets...', [selected.length]),
							callback: function(res) {
								d.hide();
								if (!res.exc) {
									frappe.show_alert({
										message: __('Successfully assigned {0} assets', [res.message ? res.message.assigned_count : selected.length]),
										indicator: 'green'
									});
									frm.events.render_assets_held_section(frm);
									frm.reload_doc();
								}
							},
							always: function() {
								d.get_primary_btn().prop('disabled', false);
							}
						});
					}
				});

				d.show();

				d.$wrapper.find('#btn-select-all-assets').on('click', function() {
					const checkboxes = d.$wrapper.find('.asset-checkbox');
					const allChecked = checkboxes.length === checkboxes.filter(':checked').length;
					checkboxes.prop('checked', !allChecked);
					$(this).text(allChecked ? __('Select All') : __('Deselect All'));
				});
			}
		});
	}
});
