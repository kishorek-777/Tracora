// Copyright (c) 2026, Kishore and contributors
// For license information, please see license.txt

frappe.provide('tracora');

tracora.check_scheduler_health = function() {
	if (!frappe.session || frappe.session.user === 'Guest') return;

	frappe.call({
		method: 'tracora.reminders.scheduler.check_scheduler_health',
		callback: function(r) {
			if (!r || !r.message) return;
			const data = r.message;
			$('#tracora-scheduler-health-banner').remove();

			const msgs = [];
			if (data.is_stale && data.stale_message) {
				msgs.push(data.stale_message);
			}
			if (data.no_recipients && data.recipient_message) {
				msgs.push(data.recipient_message);
			}

			if (msgs.length > 0) {
				const alertHtml = `
					<div id="tracora-scheduler-health-banner" class="alert alert-warning" role="alert" style="margin: 15px 20px 0 20px; border-left: 4px solid #f6ad55; font-size: 13px;">
						<div style="display: flex; align-items: center; justify-content: space-between;">
							<div>
								<strong>⚠️ Tracora Reminder System Notice:</strong>
								<ul style="margin: 4px 0 0 18px; padding: 0;">
									${msgs.map(m => `<li>${frappe.utils.escape_html(m)}</li>`).join('')}
								</ul>
							</div>
							<button type="button" class="close" data-dismiss="alert" aria-label="Close" style="font-size: 18px; line-height: 1;">
								<span aria-hidden="true">&times;</span>
							</button>
						</div>
					</div>
				`;
				const currentRoute = (frappe.get_route_str() || '').toLowerCase();
				if (currentRoute.includes('tracora') || currentRoute.startsWith('workspaces')) {
					$('.layout-main-section').first().prepend(alertHtml);
				}
			}
		}
	});
};

// Strict verification: is the current view genuinely the Tracora Workspace dashboard?
tracora.is_tracora_workspace = function() {
	if (typeof frappe === 'undefined') return false;

	// 1. If route is a List, Form, Report, Tree, etc. -> strictly NOT the workspace
	if (frappe.get_route) {
		const route = frappe.get_route();
		if (route && route.length) {
			const first = (route[0] || '').toLowerCase();
			if (['list', 'form', 'report', 'query-report', 'dashboard-view', 'print', 'tree', 'edit-workspace'].includes(first)) {
				return false;
			}
			if (first === 'workspaces' || first === 'workspace') {
				const ws_name = (route[1] || '').toLowerCase();
				return ws_name === 'tracora' || ws_name === 'private/tracora';
			}
			if (route.length === 1 && first === 'tracora') {
				return true;
			}
		}
	}

	// 2. Strict pathname verification (never loose substring matching!)
	const pathname = (window.location.pathname || '').toLowerCase().replace(/\/+$/, '');
	if (pathname.startsWith('/desk/tracora-') || pathname.startsWith('/app/tracora-')) {
		return false;
	}
	if (pathname === '/desk/tracora' || pathname === '/app/tracora') {
		return true;
	}

	// 3. Check Workspaces container visibility & active page
	const $ws = $('#page-Workspaces');
	if ($ws.length && $ws.is(':visible')) {
		const current_name = (frappe.workspace && frappe.workspace._page && frappe.workspace._page.name) || '';
		if (current_name.toLowerCase() === 'tracora') {
			return true;
		}
	}

	return false;
};

// Workspace Top Header, Status Pill, and Sidebar Subtitle Engine
tracora.setup_workspace_header = function() {
	// A. If not strictly on the Tracora Workspace dashboard, purge immediately from DOM
	if (!tracora.is_tracora_workspace()) {
		$('#tracora-topbar-status').remove();
		$('#tracora-topbar-actions').remove();
		return;
	}

	// B. Sidebar subtitle enhancement
	const $sub = $('.sidebar-header .header-subtitle, .sidebar-header .sidebar-item-label.header-subtitle, .header-subtitle, .sidebar-header-subtitle');
	if ($sub.length && $sub.text().trim() !== __('IT Asset Intelligence')) {
		$sub.text(__('IT Asset Intelligence'));
	}
	if (typeof frappe !== 'undefined' && frappe.app && frappe.app.sidebar) {
		frappe.app.sidebar.header_subtitle = __('IT Asset Intelligence');
	}

	// C. Target STRICTLY the #page-Workspaces container (never generic .page-head)
	const $ws_page = $('#page-Workspaces');
	if (!$ws_page.length || !$ws_page.is(':visible')) {
		return;
	}

	const $page_head = $ws_page.find('.page-head');
	if (!$page_head.length) return;

	// 1. Status Indicator Chip in Title Area
	const $title_area = $page_head.find('.title-area');
	if ($title_area.length && !$('#tracora-topbar-status').length) {
		$title_area.append(`
			<span id="tracora-topbar-status" class="tracora-status-chip">
				<span class="tracora-status-dot"></span>
				<span>${__('Operations Active • 706 Assets')}</span>
			</span>
		`);
	}

	// 2. Action Buttons in Page Actions (High-Impact Executive UI)
	const $actions = $page_head.find('.page-actions');
	if ($actions.length && !$('#tracora-topbar-actions').length) {
		$actions.prepend(`
			<div id="tracora-topbar-actions" class="d-flex align-items-center gap-2 mr-2">
				<button class="btn btn-sm btn-primary tracora-quickscan-btn" id="btn-tracora-quickscan" title="${__('Quick Barcode / QR Scanner (Alt + S)')}">
					<svg class="tracora-scan-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M3 7V5a2 2 0 0 1 2-2h2"></path>
						<path d="M17 3h2a2 2 0 0 1 2 2v2"></path>
						<path d="M21 17v2a2 2 0 0 1-2 2h-2"></path>
						<path d="M7 21H5a2 2 0 0 1-2-2v-2"></path>
						<line x1="7" y1="12" x2="17" y2="12" stroke="#34d399" stroke-width="2.5"></line>
					</svg>
					<span class="tracora-btn-text">${__('Quick Scan')}</span>
					<span class="tracora-kbd-badge"><kbd>Alt</kbd><span class="kbd-sep">+</span><kbd>S</kbd></span>
				</button>
				<button class="btn btn-sm btn-default tracora-mobile-btn" id="btn-tracora-mobile" title="${__('Open Tracora Mobile Scanner PWA')}">
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
						<rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect>
						<line x1="12" y1="18" x2="12.01" y2="18"></line>
					</svg>
					<span>${__('Mobile Scanner')}</span>
				</button>
			</div>
		`);

		$('#btn-tracora-quickscan').off('click').on('click', function(e) {
			e.preventDefault();
			if (tracora.open_quick_ops) tracora.open_quick_ops();
		});

		$('#btn-tracora-mobile').off('click').on('click', function(e) {
			e.preventDefault();
			window.open('/mobile', '_blank');
		});
	}
};

// Continuous polling loop (every 300ms) ensuring guaranteed presence on /desk/tracora
setInterval(function() {
	tracora.setup_workspace_header();
}, 300);

$(document).on('page-change', function() {
	const route = (frappe.get_route_str() || '').toLowerCase();
	if (route.includes('tracora') || route.startsWith('workspaces')) {
		tracora.check_scheduler_health();
	}
	tracora.setup_workspace_header();
});

if (typeof frappe !== 'undefined' && frappe.router) {
	frappe.router.on('change', function() {
		tracora.setup_workspace_header();
	});
}

// Global Hotkeys: Alt + S or Ctrl + Shift + S triggers Quick Ops
$(document).on('keydown', function(e) {
	if ((e.altKey && (e.key === 's' || e.key === 'S')) ||
		(e.ctrlKey && e.shiftKey && (e.key === 'S' || e.key === 's'))) {
		const targetTag = (e.target && e.target.tagName) || '';
		if (!['INPUT', 'TEXTAREA'].includes(targetTag.toUpperCase()) || e.ctrlKey) {
			e.preventDefault();
			if (tracora.open_quick_ops) {
				tracora.open_quick_ops();
			}
		}
	}
});
