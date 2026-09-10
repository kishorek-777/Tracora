// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tracora Asset', {
	setup: function(frm) {
		frm.set_query('owner_company', function() {
			return { filters: {} };
		});
		frm.set_query('holding_company', function() {
			return { filters: {} };
		});
		frm.set_query('branch', function() {
			if (frm.doc.holding_company) {
				return { filters: { company: frm.doc.holding_company } };
			}
			return {};
		});
		frm.set_query('point_of_contact', function() {
			return { filters: { status: ['!=', 'Exited'] } };
		});
	},

	refresh: function(frm) {
		frm.trigger('toggle_tag_field');

		if (!frm.is_new()) {
			frm.set_df_property('owner_company', 'read_only', 1);

			const status_colors = {
				'In Store': 'blue',
				'Assigned': 'green',
				'Under Maintenance': 'orange',
				'Damaged': 'orange',
				'Lost': 'red',
				'Recovered': 'yellow',
				'Released': 'grey',
				'Retired': 'grey'
			};
			const color = status_colors[frm.doc.status] || 'grey';
			frm.page.set_indicator(__(frm.doc.status), color);

			// Status-dependent buttons
			frm.clear_custom_buttons();

			const print_btn_text = frm.doc.label_printed_on ? __('Reprint label') : __('Print Label');
			const add_print_button = () => {
				const btn = frm.add_custom_button(print_btn_text, function() {
					frm.events.print_label(frm);
				});
				if (frm.doc.label_printed_on) {
					btn.attr('title', __('Last printed on {0}', [frappe.datetime.str_to_user(frm.doc.label_printed_on)]));
				}
				return btn;
			};

			if (frm.doc.status === 'In Store') {
				frm.add_custom_button(__('Assign'), function() {
					frm.events.show_assign_dialog(frm);
				}).addClass('btn-primary');
				frm.add_custom_button(__('Send to Maintenance'), function() {
					frm.events.send_to_maintenance(frm);
				});
				add_print_button();
			} else if (frm.doc.status === 'Assigned') {
				frm.add_custom_button(__('Unassign'), function() {
					frm.events.show_unassign_dialog(frm);
				}).addClass('btn-primary');
				frm.add_custom_button(__('Send to Maintenance'), function() {
					frm.events.send_to_maintenance(frm);
				});
				add_print_button();
			} else if (frm.doc.status === 'Under Maintenance') {
				// Fetch open maintenance details for prominent banner and close action
				frappe.call({
					method: 'tracora.api.maintenance.get_open_maintenance',
					args: { asset: frm.doc.name },
					callback: function(r) {
						if (r.message) {
							const log = r.message;
							const sent_date = frappe.datetime.str_to_user(log.date_sent);
							const expected_date = log.due_date ? frappe.datetime.str_to_user(log.due_date) : __('Not Specified');
							
							frm.dashboard.clear_headline();
							frm.dashboard.set_headline(
								`<div class="d-flex justify-content-between align-items-center">
									<span><strong>⚠️ Asset Under Maintenance:</strong> At <b>${frappe.utils.escape_html(log.vendor)}</b> since <b>${sent_date}</b> — expected back <b>${expected_date}</b>.</span>
									<button class="btn btn-xs btn-primary ml-3" id="btn-close-maint-banner">${__('Close Maintenance')}</button>
								</div>`,
								'orange'
							);

							// Bind click handler for banner button
							setTimeout(() => {
								$('#btn-close-maint-banner').off('click').on('click', () => {
									frm.events.show_close_maintenance_dialog(frm, log.name);
								});
							}, 200);

							frm.add_custom_button(__('Close Maintenance'), function() {
								frm.events.show_close_maintenance_dialog(frm, log.name);
							}).addClass('btn-primary');
						}
					}
				});
				add_print_button();
			} else if (frm.doc.status === 'Lost') {
				frm.dashboard.clear_headline();
				frm.add_custom_button(__('Recover'), function() {
					frm.events.show_recover_dialog(frm);
				}).addClass('btn-primary');
			} else {
				frm.dashboard.clear_headline();
			}

			if (frm.doc.label_printed_on && frm.doc.status !== 'Under Maintenance') {
				frm.dashboard.set_headline(
					`<span><strong>🏷️ Label printed:</strong> ${frappe.datetime.str_to_user(frm.doc.label_printed_on)}</span>`,
					'blue'
				);
			}

			// Any status: Transfer Ownership
			frm.add_custom_button(__('Transfer Ownership'), function() {
				frm.events.show_transfer_ownership_dialog(frm);
			}, __('Actions'));

			frm.add_custom_button(__('View Movement History'), function() {
				frappe.set_route('List', 'Tracora Asset Movement', { asset: frm.doc.name });
			}, __('Actions'));

			// Narrative Movement Timeline
			frm.events.render_movement_timeline(frm);
			frm.events.render_installed_licences(frm);
		}
	},

	tag_mode: function(frm) {
		frm.trigger('toggle_tag_field');
	},

	toggle_tag_field: function(frm) {
		if (frm.doc.tag_mode === 'Manual entry') {
			frm.set_df_property('asset_tag', 'read_only', 0);
			frm.set_df_property('asset_tag', 'reqd', 1);
		} else {
			frm.set_df_property('asset_tag', 'read_only', 1);
			frm.set_df_property('asset_tag', 'reqd', 0);
		}
	},

	show_assign_dialog: function(frm) {
		let chosen_employee = null;

		const d = new frappe.ui.Dialog({
			title: __('Assign Asset: {0}', [frm.doc.asset_tag || frm.doc.name]),
			fields: [
				{
					fieldname: 'employee',
					fieldtype: 'Link',
					label: __('Employee'),
					options: 'Tracora Employee',
					reqd: 1,
					get_query: function() {
						return { filters: { status: ['!=', 'Exited'] } };
					},
					change: function() {
						const emp_id = d.get_value('employee');
						if (emp_id) {
							frappe.db.get_value('Tracora Employee', emp_id, ['employee_name', 'company', 'branch', 'department'])
								.then(r => {
									if (r && r.message) {
										chosen_employee = r.message;
										d.set_value('emp_company', r.message.company || '');
										d.set_value('emp_branch', r.message.branch || '');
										d.set_value('emp_department', r.message.department || '');
									}
								});
						} else {
							chosen_employee = null;
							d.set_value('emp_company', '');
							d.set_value('emp_branch', '');
							d.set_value('emp_department', '');
						}
					}
				},
				{
					fieldname: 'col_break_1',
					fieldtype: 'Column Break'
				},
				{
					fieldname: 'emp_company',
					fieldtype: 'Data',
					label: __('Company'),
					read_only: 1
				},
				{
					fieldname: 'emp_branch',
					fieldtype: 'Data',
					label: __('Branch'),
					read_only: 1
				},
				{
					fieldname: 'emp_department',
					fieldtype: 'Data',
					label: __('Department'),
					read_only: 1
				},
				{
					fieldname: 'sec_break_ref',
					fieldtype: 'Section Break'
				},
				{
					fieldname: 'reference',
					fieldtype: 'Data',
					label: __('Reference / Ticket ID')
				}
			],
			primary_action_label: __('Assign Asset'),
			primary_action: function(values) {
				if (!values.employee) {
					frappe.msgprint(__('Please select an employee to assign.'));
					return;
				}
				d.get_primary_btn().prop('disabled', true);
				frappe.call({
					method: 'tracora.api.assign.assign_asset',
					args: {
						asset: frm.doc.name,
						employee: values.employee,
						reference: values.reference
					},
					freeze: true,
					freeze_message: __('Assigning Asset...'),
					callback: function(r) {
						d.hide();
						if (!r.exc) {
							frappe.show_alert({ message: __('Asset successfully assigned'), indicator: 'green' });
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
	},

	show_unassign_dialog: function(frm) {
		const d = new frappe.ui.Dialog({
			title: __('Unassign Asset: {0}', [frm.doc.asset_tag || frm.doc.name]),
			fields: [
				{
					fieldname: 'current_holder',
					fieldtype: 'Data',
					label: __('Current Holder'),
					default: frm.doc.assigned_to,
					read_only: 1
				},
				{
					fieldname: 'location',
					fieldtype: 'Link',
					label: __('Return Location'),
					options: 'Tracora Location',
					reqd: 1,
					default: frm.doc.location
				},
				{
					fieldname: 'condition',
					fieldtype: 'Select',
					label: __('Condition on Return'),
					options: ['New', 'Good', 'Fair', 'Poor', 'Not Working'],
					default: frm.doc.condition || 'Good',
					reqd: 1
				},
				{
					fieldname: 'status',
					fieldtype: 'Select',
					label: __('Status Override'),
					options: ['In Store', 'Damaged', 'Under Maintenance', 'Lost'],
					default: 'In Store',
					reqd: 1
				},
				{
					fieldname: 'remarks',
					fieldtype: 'Small Text',
					label: __('Remarks (Mandatory)'),
					reqd: 1
				}
			],
			primary_action_label: __('Confirm Unassign'),
			primary_action: function(values) {
				if (!values.remarks || !values.remarks.trim()) {
					frappe.msgprint({
						title: __('Validation Error'),
						message: __('Remarks are mandatory when unassigning an asset (FR-51).'),
						indicator: 'red'
					});
					return;
				}
				if (!values.location) {
					frappe.msgprint({
						title: __('Validation Error'),
						message: __('Return location is mandatory (FR-52).'),
						indicator: 'red'
					});
					return;
				}
				d.get_primary_btn().prop('disabled', true);
				frappe.call({
					method: 'tracora.api.assign.unassign_asset',
					args: {
						asset: frm.doc.name,
						location: values.location,
						remarks: values.remarks,
						condition: values.condition,
						status: values.status
					},
					freeze: true,
					freeze_message: __('Unassigning Asset...'),
					callback: function(r) {
						d.hide();
						if (!r.exc) {
							frappe.show_alert({ message: __('Asset successfully unassigned'), indicator: 'green' });
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
	},

	show_transfer_ownership_dialog: function(frm) {
		const d = new frappe.ui.Dialog({
			title: __('Transfer Ownership: {0}', [frm.doc.asset_tag || frm.doc.name]),
			fields: [
				{
					fieldname: 'current_owner',
					fieldtype: 'Data',
					label: __('Current Owner'),
					default: frm.doc.owner_company,
					read_only: 1
				},
				{
					fieldname: 'to_owner',
					fieldtype: 'Link',
					label: __('New Owner Company'),
					options: 'Tracora Company',
					reqd: 1,
					get_query: function() {
						return { filters: { name: ['!=', frm.doc.owner_company] } };
					}
				},
				{
					fieldname: 'reason',
					fieldtype: 'Small Text',
					label: __('Reason for Transfer (FR-82)'),
					reqd: 1
				}
			],
			primary_action_label: __('Transfer Ownership'),
			primary_action: function(values) {
				if (!values.reason || !values.reason.trim()) {
					frappe.msgprint(__('Reason is required for ownership transfer (FR-82).'));
					return;
				}
				d.get_primary_btn().prop('disabled', true);
				frappe.call({
					method: 'tracora.api.assign.transfer_ownership',
					args: {
						asset: frm.doc.name,
						to_owner: values.to_owner,
						reason: values.reason
					},
					freeze: true,
					freeze_message: __('Transferring Ownership...'),
					callback: function(r) {
						d.hide();
						if (!r.exc) {
							frappe.show_alert({ message: __('Ownership transferred successfully'), indicator: 'green' });
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
	},

	show_recover_dialog: function(frm) {
		const d = new frappe.ui.Dialog({
			title: __('Recover Lost Asset: {0}', [frm.doc.asset_tag || frm.doc.name]),
			fields: [
				{
					fieldname: 'condition',
					fieldtype: 'Select',
					label: __('Condition on Recovery'),
					options: ['New', 'Good', 'Fair', 'Poor', 'Not Working'],
					default: 'Good',
					reqd: 1
				},
				{
					fieldname: 'remarks',
					fieldtype: 'Small Text',
					label: __('Recovery Remarks (FR-84)'),
					reqd: 1
				}
			],
			primary_action_label: __('Recover Asset'),
			primary_action: function(values) {
				if (!values.remarks || !values.remarks.trim()) {
					frappe.msgprint(__('Remarks are required when recovering a lost asset (FR-84).'));
					return;
				}
				d.get_primary_btn().prop('disabled', true);
				frappe.call({
					method: 'tracora.api.assign.recover_asset',
					args: {
						asset: frm.doc.name,
						remarks: values.remarks,
						condition: values.condition
					},
					freeze: true,
					freeze_message: __('Recovering Asset...'),
					callback: function(r) {
						d.hide();
						if (!r.exc) {
							frappe.show_alert({ message: __('Asset recovered successfully'), indicator: 'green' });
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
	},

	print_label: function(frm) {
		frappe.call({
			method: 'tracora.api.labels.print_labels',
			args: { assets: [frm.doc.name] },
			freeze: true,
			freeze_message: __('Preparing label...'),
			callback: function(r) {
				if (r.message && r.message.html) {
					const print_win = window.open('', '_blank');
					if (print_win) {
						print_win.document.open();
						print_win.document.write(r.message.html);
						print_win.document.close();
						print_win.focus();
						setTimeout(() => {
							print_win.print();
						}, 350);
					} else {
						frappe.msgprint(__('Please allow popups to print labels.'));
					}
					frm.reload_doc();
				}
			}
		});
	},

	send_to_maintenance: function(frm) {
		const d = new frappe.ui.Dialog({
			title: __('Send Asset to Maintenance: {0}', [frm.doc.asset_tag || frm.doc.name]),
			fields: [
				{
					fieldname: 'vendor',
					fieldtype: 'Data',
					label: __('Vendor / Handler'),
					reqd: 1,
				},
				{
					fieldname: 'reason',
					fieldtype: 'Small Text',
					label: __('Reason for Maintenance'),
					reqd: 1,
				},
				{
					fieldname: 'date_sent',
					fieldtype: 'Date',
					label: __('Date Sent'),
					default: frappe.datetime.get_today(),
					reqd: 1,
				},
				{
					fieldname: 'due_date',
					fieldtype: 'Date',
					label: __('Expected Return Date'),
					description: __('Drives automated maintenance-due reminders (FR-25).'),
				},
			],
			primary_action_label: __('Confirm Dispatch'),
			primary_action: function(values) {
				if (!values.vendor || !values.vendor.trim()) {
					frappe.msgprint(__('Vendor / Handler is mandatory.'));
					return;
				}
				if (!values.reason || !values.reason.trim()) {
					frappe.msgprint(__('Reason is mandatory.'));
					return;
				}
				d.get_primary_btn().prop('disabled', true);
				frappe.call({
					method: 'tracora.api.maintenance.send_to_maintenance',
					args: {
						asset: frm.doc.name,
						vendor: values.vendor,
						reason: values.reason,
						date_sent: values.date_sent,
						due_date: values.due_date,
					},
					freeze: true,
					freeze_message: __('Dispatching to Maintenance...'),
					callback: function(r) {
						d.hide();
						if (!r.exc) {
							frappe.show_alert({ message: __('Asset successfully dispatched to maintenance'), indicator: 'orange' });
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
	},

	show_close_maintenance_dialog: function(frm, log_name) {
		const d = new frappe.ui.Dialog({
			title: __('Close Maintenance: {0}', [frm.doc.asset_tag || frm.doc.name]),
			fields: [
				{
					fieldname: 'condition_on_return',
					fieldtype: 'Select',
					label: __('Condition on Return'),
					options: ['New', 'Good', 'Fair', 'Poor', 'Not Working'],
					default: frm.doc.condition || 'Good',
					reqd: 1,
				},
				{
					fieldname: 'date_returned',
					fieldtype: 'Date',
					label: __('Date Returned'),
					default: frappe.datetime.get_today(),
					reqd: 1,
				},
				{
					fieldname: 'is_beyond_repair',
					fieldtype: 'Check',
					label: __('Beyond Repair (Retire Asset)'),
				},
				{
					fieldname: 'remarks',
					fieldtype: 'Small Text',
					label: __('Closing Remarks'),
				},
			],
			primary_action_label: __('Confirm Return'),
			primary_action: function(values) {
				if (!values.is_beyond_repair && !values.condition_on_return) {
					frappe.msgprint(__('Condition on return is required (FR-18).'));
					return;
				}
				d.get_primary_btn().prop('disabled', true);
				frappe.call({
					method: 'tracora.api.maintenance.close_maintenance',
					args: {
						log_name: log_name,
						condition_on_return: values.condition_on_return,
						date_returned: values.date_returned,
						is_beyond_repair: values.is_beyond_repair,
						remarks: values.remarks,
					},
					freeze: true,
					freeze_message: __('Closing Maintenance...'),
					callback: function(r) {
						d.hide();
						if (!r.exc) {
							frappe.show_alert({ message: __('Maintenance closed successfully'), indicator: 'green' });
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
	},

	render_movement_timeline: function(frm) {
		frappe.call({
			method: 'tracora.api.assign.get_movement_history',
			args: { asset: frm.doc.name },
			callback: function(r) {
				if (!r.message || !r.message.length) {
					return;
				}
				const movements = r.message;

				const badge_styles = {
					'Assign': 'background-color: #2b6cb0; color: white;',
					'Unassign': 'background-color: #c05621; color: white;',
					'Ownership Transfer': 'background-color: #6b46c1; color: white;',
					'Recovered': 'background-color: #285e61; color: white;',
					'Exit Release': 'background-color: #9c4221; color: white;',
					'Location Change': 'background-color: #2c7a7b; color: white;',
					'Maintenance Sent': 'background-color: #b7791f; color: white;',
					'Maintenance Returned': 'background-color: #276749; color: white;',
					'Beyond Repair': 'background-color: #742a2a; color: white;',
					'Status Change': 'background-color: #4a5568; color: white;',
					'Label Reprint': 'background-color: #718096; color: white;'
				};

				let items_html = movements.map(m => {
					const badge_style = badge_styles[m.movement_type] || 'background-color: #4a5568; color: white;';
					const remarks_html = m.remarks ? `<div class="text-muted mt-1" style="font-style: italic;">Remarks: ${frappe.utils.escape_html(m.remarks)}</div>` : '';
					return `
						<li class="list-group-item px-3 py-2" style="border-left: 3px solid #3182ce; margin-bottom: 6px; border-radius: 4px; background: var(--card-bg, #f7fafc);">
							<div class="d-flex justify-content-between align-items-center">
								<div>
									<span class="badge mr-2" style="${badge_style}; font-size: 11px; padding: 4px 8px; border-radius: 4px;">${frappe.utils.escape_html(m.movement_type)}</span>
									<span style="font-size: 13px; font-weight: 500;">${frappe.utils.escape_html(m.sentence)}</span>
								</div>
								<span class="text-muted" style="font-size: 11px;">${frappe.datetime.comment_when(m.movement_date || m.creation)}</span>
							</div>
							${remarks_html}
						</li>
					`;
				}).join('');

				const timeline_html = `
					<div class="tracora-movement-history my-3">
						<div class="d-flex justify-content-between align-items-center mb-2">
							<h6 class="text-muted uppercase mb-0" style="font-size: 12px; font-weight: 600; letter-spacing: 0.5px;">Movement History (${movements.length})</h6>
							<a href="/desk/tracora-asset-movement?asset=${encodeURIComponent(frm.doc.name)}" class="text-muted" style="font-size: 11px; font-weight: 500; text-decoration: underline;">View in Asset Movements &rarr;</a>
						</div>
						<ul class="list-group list-group-flush">
							${items_html}
						</ul>
					</div>
				`;

				if (!frm.timeline_wrapper) {
					frm.timeline_wrapper = $('<div class="tracora-timeline-container p-3 my-2" style="background: var(--fg-color, #fff); border: 1px solid var(--border-color, #e2e8f0); border-radius: 6px;"></div>');
					frm.dashboard.wrapper.append(frm.timeline_wrapper);
				}
				frm.timeline_wrapper.html(timeline_html);
			}
		});
	},

	render_installed_licences: function(frm) {
		if (frm.is_new()) return;
		frappe.call({
			method: 'tracora.licences.seats.get_installed_licences',
			args: {
				asset: frm.doc.name
			},
			callback: function(r) {
				const seats = r.message || [];
				if (!seats.length) {
					if (frm.software_licences_wrapper) {
						frm.software_licences_wrapper.html('');
					}
					return;
				}

				const badge_colors = {
					'Active': '#2b6cb0',
					'Flagged': '#c05621',
					'Released': '#718096'
				};

				const items_html = seats.map(s => {
					const badge_color = badge_colors[s.seat_status] || '#718096';
					const user_str = s.user ? ` &bull; User: <b>${frappe.utils.escape_html(s.user)}</b>` : ' &bull; <i>No user assigned</i>';
					const reason_str = s.flagged_reason ? `<div class="text-muted mt-1" style="font-size: 11px; font-style: italic;">Reason: ${frappe.utils.escape_html(s.flagged_reason)}</div>` : '';
					return `
						<li class="list-group-item px-3 py-2" style="border-left: 3px solid ${badge_color}; margin-bottom: 6px; border-radius: 4px; background: var(--card-bg, #f7fafc);">
							<div class="d-flex justify-content-between align-items-center">
								<div>
									<span class="badge mr-2" style="background-color: ${badge_color}; color: white; font-size: 11px; padding: 4px 8px; border-radius: 4px;">${frappe.utils.escape_html(s.seat_status)}</span>
									<span style="font-size: 13px; font-weight: 500;">
										<a href="/app/tracora-software-licence/${encodeURIComponent(s.parent)}" style="text-decoration: underline;">${frappe.utils.escape_html(s.parent)}</a>
										${user_str}
									</span>
								</div>
								<span class="text-muted" style="font-size: 11px;">Seat #${frappe.utils.escape_html(s.name)}</span>
							</div>
							${reason_str}
						</li>
					`;
				}).join('');

				const licences_html = `
					<div class="tracora-installed-licences my-3">
						<div class="d-flex justify-content-between align-items-center mb-2">
							<h6 class="text-muted uppercase mb-0" style="font-size: 12px; font-weight: 600; letter-spacing: 0.5px;">Installed Software Licences (${seats.length})</h6>
						</div>
						<ul class="list-group list-group-flush">
							${items_html}
						</ul>
					</div>
				`;

				if (!frm.software_licences_wrapper) {
					frm.software_licences_wrapper = $('<div class="tracora-licences-container p-3 my-2" style="background: var(--fg-color, #fff); border: 1px solid var(--border-color, #e2e8f0); border-radius: 6px;"></div>');
					frm.dashboard.wrapper.append(frm.software_licences_wrapper);
				}
				frm.software_licences_wrapper.html(licences_html);
			}
		});
	},
});