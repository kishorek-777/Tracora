// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tracora Vendor Contract', {
	refresh(frm) {
		// Status indicators
		const status_colors = {
			'Upcoming': 'green',
			'Due Soon': 'orange',
			'Overdue': 'red',
			'Completed / One-off': 'blue',
			'Closed / Terminated': 'gray'
		};
		if (frm.doc.renewal_status && status_colors[frm.doc.renewal_status]) {
			frm.page.set_indicator(frm.doc.renewal_status, status_colors[frm.doc.renewal_status]);
		}

		if (!frm.is_new() && frm.doc.renewal_status !== 'Closed / Terminated') {
			frm.add_custom_button(__('Log Payment'), function() {
				const d = new frappe.ui.Dialog({
					title: __('Record Payment / Renewal'),
					fields: [
						{
							label: __('Payment Date'),
							fieldname: 'payment_date',
							fieldtype: 'Date',
							default: frappe.datetime.get_today(),
							reqd: 1
						},
						{
							label: __('Amount Paid'),
							fieldname: 'amount_paid',
							fieldtype: 'Currency',
							options: frm.doc.currency || 'INR',
							default: frm.doc.expected_amount || 0,
							reqd: 1
						},
						{
							label: __('Payment Mode'),
							fieldname: 'payment_mode',
							fieldtype: 'Select',
							options: 'Bank Transfer / NEFT\nUPI\nCorporate Card\nNet Banking\nCheque\nCash',
							default: 'Bank Transfer / NEFT',
							reqd: 1
						},
						{
							label: __('UTR / Reference No'),
							fieldname: 'reference_no',
							fieldtype: 'Data'
						},
						{
							label: __('Invoice / Receipt Attachment'),
							fieldname: 'invoice_file',
							fieldtype: 'Attach'
						},
						{
							label: __('Remarks'),
							fieldname: 'remarks',
							fieldtype: 'Small Text'
						}
					],
					primary_action_label: __('Submit Payment'),
					primary_action(values) {
						if (!values.amount_paid || parseFloat(values.amount_paid) <= 0) {
							frappe.msgprint(__('Amount Paid must be greater than zero.'));
							return;
						}

						frappe.call({
							doc: frm.doc,
							method: 'log_payment',
							args: {
								payment_date: values.payment_date,
								amount_paid: values.amount_paid,
								payment_mode: values.payment_mode,
								reference_no: values.reference_no,
								invoice_file: values.invoice_file,
								remarks: values.remarks
							},
							freeze: true,
							freeze_message: __('Recording payment and updating renewal schedule...'),
							callback: function(r) {
								d.hide();
								if (r.message && r.message.success) {
									frappe.show_alert({
										message: __('Payment recorded successfully! Next renewal: {0}', [r.message.next_renewal_date || 'N/A']),
										indicator: 'green'
									});
									frm.reload_doc();
								}
							}
						});
					}
				});
				d.show();
			}).addClass('btn-primary');
		}
	}
});

