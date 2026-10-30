// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.provide('tracora');

tracora.open_quick_ops = function(initial_tag) {
	let selected_asset = null;
	let media_stream = null;
	let scan_anim_id = null;
	let is_detecting = false;

	// Audio Chime Synthesizer via Web Audio API (Zero external assets needed)
	function play_scan_sound(success) {
		try {
			const AudioContext = window.AudioContext || window.webkitAudioContext;
			if (!AudioContext) return;
			const ctx = new AudioContext();
			const osc = ctx.createOscillator();
			const gain = ctx.createGain();
			osc.connect(gain);
			gain.connect(ctx.destination);

			if (success) {
				// High futuristic confirmation double-chime (880Hz -> 1760Hz)
				osc.type = 'sine';
				osc.frequency.setValueAtTime(880, ctx.currentTime);
				osc.frequency.setValueAtTime(1760, ctx.currentTime + 0.08);
				gain.gain.setValueAtTime(0.15, ctx.currentTime);
				gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.22);
				osc.start(ctx.currentTime);
				osc.stop(ctx.currentTime + 0.22);
			} else {
				// Gentle low advisory buzzer
				osc.type = 'sawtooth';
				osc.frequency.setValueAtTime(220, ctx.currentTime);
				gain.gain.setValueAtTime(0.2, ctx.currentTime);
				gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
				osc.start(ctx.currentTime);
				osc.stop(ctx.currentTime + 0.25);
			}
		} catch (e) {
			// Web Audio not permitted or muted
		}
	}

	const d = new frappe.ui.Dialog({
		title: __('⚡ Quick Asset Operations'),
		fields: [
			{
				label: __('Asset Tag / Serial / Barcode'),
				fieldname: 'scan_input',
				fieldtype: 'Data',
				reqd: 0,
				description: __('Laser scanner wedge, laptop camera, or typed tag.')
			},
			{
				fieldtype: 'HTML',
				fieldname: 'camera_toggle_html'
			},
			{
				fieldtype: 'HTML',
				fieldname: 'camera_view_html'
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

	// Setup Camera Toggle UI
	const camera_toggle_container = d.fields_dict.camera_toggle_html.$wrapper;
	camera_toggle_container.html(`
		<div class="d-flex justify-content-between align-items-center mb-2" style="font-size: 12px;">
			<span class="text-muted">
				<i class="fa fa-barcode mr-1"></i> ${__('Physical laser guns scan directly into the field above.')}
			</span>
			<button class="btn btn-xs btn-default" id="btn-toggle-camera" style="border-radius: 6px; font-weight: 600;">
				📷 ${__('Scan with Laptop Camera')}
			</button>
		</div>
	`);

	const camera_view_container = d.fields_dict.camera_view_html.$wrapper;

	function stop_camera() {
		if (scan_anim_id) {
			cancelAnimationFrame(scan_anim_id);
			scan_anim_id = null;
		}
		is_detecting = false;
		if (media_stream) {
			media_stream.getTracks().forEach(track => track.stop());
			media_stream = null;
		}
		camera_view_container.empty();
		$('#btn-toggle-camera').html(`📷 ${__('Scan with Laptop Camera')}`).removeClass('btn-danger').addClass('btn-default');
	}

	async function start_camera() {
		try {
			camera_view_container.html(`
				<div class="tracora-webcam-container">
					<div class="tracora-reticle-corner tracora-reticle-tl"></div>
					<div class="tracora-reticle-corner tracora-reticle-tr"></div>
					<div class="tracora-reticle-corner tracora-reticle-bl"></div>
					<div class="tracora-reticle-corner tracora-reticle-br"></div>
					<div class="tracora-laser-line"></div>
					<video id="tracora-scanner-video" class="tracora-webcam-video" autoplay playsinline muted></video>
					<div style="position: absolute; bottom: 8px; left: 0; right: 0; text-align: center; color: #38bdf8; font-size: 11px; font-weight: 600; text-shadow: 0 1px 3px rgba(0,0,0,0.8); z-index: 11;">
						${__('Align Barcode or QR Code within the cyber reticle')}
					</div>
				</div>
			`);

			$('#btn-toggle-camera').html(`🛑 ${__('Stop Camera')}`).removeClass('btn-default').addClass('btn-danger');

			// Request Camera: prioritize environment, fallback to user (laptop webcam)
			let stream;
			try {
				stream = await navigator.mediaDevices.getUserMedia({
					video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }
				});
			} catch (err) {
				stream = await navigator.mediaDevices.getUserMedia({ video: true });
			}

			media_stream = stream;
			const video = document.getElementById('tracora-scanner-video');
			if (!video) return;
			video.srcObject = stream;
			await video.play();

			// Continuous detection loop using native BarcodeDetector API if available
			if ('BarcodeDetector' in window) {
				const barcodeDetector = new window.BarcodeDetector({
					formats: ['qr_code', 'code_128', 'code_39', 'ean_13', 'ean_8', 'data_matrix', 'upc_a', 'upc_e']
				});

				is_detecting = true;
				let last_check = 0;

				async function scan_frame(timestamp) {
					if (!is_detecting || !video || video.readyState < 2) {
						if (is_detecting) scan_anim_id = requestAnimationFrame(scan_frame);
						return;
					}

					// Throttle barcode analysis every 160ms for smooth performance
					if (timestamp - last_check > 160) {
						last_check = timestamp;
						try {
							const barcodes = await barcodeDetector.detect(video);
							if (barcodes && barcodes.length > 0) {
								const raw_val = barcodes[0].rawValue;
								if (raw_val) {
									stop_camera();
									play_scan_sound(true);
									d.set_value('scan_input', raw_val);
									lookup_asset(raw_val);
									return;
								}
							}
						} catch (e) {
							// Frame decode failure or blur, continue scanning
						}
					}
					if (is_detecting) {
						scan_anim_id = requestAnimationFrame(scan_frame);
					}
				}
				scan_anim_id = requestAnimationFrame(scan_frame);
			} else {
				// Older browsers without native BarcodeDetector: provide manual snap/hint
				frappe.show_alert({
					message: __('Native camera barcode reader active. Hold code steady.'),
					indicator: 'blue'
				});
			}
		} catch (err) {
			console.error('Camera access error:', err);
			frappe.msgprint({
				title: __('Camera Access Denied or Unavailable'),
				message: __('Could not access laptop camera. Please verify browser camera permissions, or use a handheld barcode scanner.'),
				indicator: 'red'
			});
			stop_camera();
		}
	}

	$('#btn-toggle-camera').on('click', function(e) {
		e.preventDefault();
		if (media_stream) {
			stop_camera();
		} else {
			start_camera();
		}
	});

	// Cleanup video stream when modal closes
	d.$wrapper.on('hidden.bs.modal', function() {
		stop_camera();
	});

	function lookup_asset(query_str) {
		const preview_container = d.fields_dict.asset_preview_html.$wrapper;
		preview_container.html(`
			<div class="text-center p-4 text-muted">
				<div class="spinner-border spinner-border-sm mr-2" role="status"></div>
				${__('Locating hardware record...')}
			</div>
		`);

		// Search asset by asset_tag, serial_no, or doc name
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
								play_scan_sound(true);
								render_asset_card(asset);
							}
						}
					});
				} else {
					play_scan_sound(true);
					render_asset_card(asset);
				}
			}
		});
	}

	function render_not_found(query_str) {
		play_scan_sound(false);
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
