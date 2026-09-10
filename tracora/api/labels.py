# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import escape_html, now_datetime
from tracora.tags.qr import qr_base64


def _get_label_settings():
	"""Fetch physical dimensions from Tracora Settings with safe fallbacks."""
	width = frappe.db.get_single_value("Tracora Settings", "label_width_mm") or 50.0
	height = frappe.db.get_single_value("Tracora Settings", "label_height_mm") or 25.0
	qr_size = frappe.db.get_single_value("Tracora Settings", "qr_size_mm") or 15.0
	return float(width), float(height), float(qr_size)


def _render_single_label_body(label: dict, width_mm: float, height_mm: float, qr_size_mm: float) -> str:
	"""Render the inner HTML for a single 50 x 25 mm label sticker."""
	asset_tag = escape_html(label.get("asset_tag") or "")
	asset_name = escape_html(label.get("asset_name") or "")
	qr_code = label.get("qr_code") or ""

	return f"""
	<div class="label-page" style="width: {width_mm}mm; height: {height_mm}mm;">
		<div class="label-qr-col" style="width: {qr_size_mm}mm; height: {qr_size_mm}mm;">
			<img class="label-qr-img" src="{qr_code}" alt="{asset_tag}" style="width: {qr_size_mm}mm; height: {qr_size_mm}mm;" />
		</div>
		<div class="label-text-col">
			<div class="label-tag">{asset_tag}</div>
			<div class="label-name" title="{asset_name}">{asset_name}</div>
		</div>
	</div>
	"""


def render_combined_html(labels: list[dict], width_mm: float, height_mm: float, qr_size_mm: float) -> str:
	"""Render full standalone printable document containing all labels with print media styling."""
	body_labels = "\n".join(
		_render_single_label_body(l, width_mm, height_mm, qr_size_mm) for l in labels
	)

	label_count = len(labels)
	count_suffix = f"({label_count} label{'s' if label_count > 1 else ''})"

	return f"""<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<title>Tracora Asset Labels</title>
	<style>
		@page {{
			size: {width_mm}mm {height_mm}mm;
			margin: 0 !important;
		}}
		* {{
			box-sizing: border-box;
		}}
		html, body {{
			margin: 0 !important;
			padding: 0 !important;
			background: #ffffff;
			color: #000000 !important;
			-webkit-print-color-adjust: exact;
			print-color-adjust: exact;
		}}
		@media screen {{
			body {{
				background-color: #f3f4f6 !important;
				padding: 24px 16px !important;
				display: flex !important;
				flex-direction: column !important;
				align-items: center !important;
				font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
			}}
			.print-bar {{
				background: #ffffff;
				border: 1px solid #e5e7eb;
				border-radius: 8px;
				padding: 14px 18px;
				margin-bottom: 20px;
				max-width: 520px;
				width: 100%;
				box-shadow: 0 1px 3px rgba(0,0,0,0.1);
				display: flex;
				flex-direction: column;
				gap: 10px;
			}}
			.print-bar-header {{
				display: flex;
				justify-content: space-between;
				align-items: center;
			}}
			.print-btn {{
				background: #111827;
				color: #ffffff;
				border: none;
				border-radius: 6px;
				padding: 7px 14px;
				font-size: 13px;
				font-weight: 600;
				cursor: pointer;
				transition: background 0.15s;
			}}
			.print-btn:hover {{
				background: #374151;
			}}
			.print-tips {{
				font-size: 12px;
				color: #4b5563;
				background: #fef3c7;
				border: 1px solid #fde68a;
				border-radius: 6px;
				padding: 8px 12px;
				line-height: 1.45;
			}}
			.label-page {{
				margin: 10px auto !important;
				box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
				border: 1px solid #d1d5db !important;
				border-radius: 4px;
			}}
		}}
		@media print {{
			.no-print {{
				display: none !important;
			}}
			html, body {{
				margin: 0 !important;
				padding: 0 !important;
				background: #ffffff !important;
				width: {width_mm}mm !important;
				height: {height_mm}mm !important;
			}}
			.label-page {{
				margin: 0 !important;
				border: none !important;
				box-shadow: none !important;
				page-break-after: always;
				break-after: page;
			}}
			.label-page:last-child {{
				page-break-after: avoid;
				break-after: avoid;
			}}
		}}
		.label-page {{
			box-sizing: border-box;
			overflow: hidden;
			padding: 1.5mm 2mm;
			display: flex;
			flex-direction: row;
			align-items: center;
			background: #ffffff;
		}}
		.label-qr-col {{
			flex-shrink: 0;
			display: flex;
			align-items: center;
			justify-content: center;
			margin-right: 2.5mm;
		}}
		.label-qr-img {{
			image-rendering: pixelated;
			image-rendering: -moz-crisp-edges;
			image-rendering: crisp-edges;
			object-fit: contain;
			display: block;
		}}
		.label-text-col {{
			flex: 1;
			min-width: 0;
			display: flex;
			flex-direction: column;
			justify-content: center;
			overflow: hidden;
		}}
		.label-tag {{
			font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
			font-size: 11pt;
			font-weight: 700;
			letter-spacing: 0.5px;
			line-height: 1.2;
			color: #000000;
			white-space: nowrap;
			overflow: hidden;
			text-overflow: ellipsis;
		}}
		.label-name {{
			font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
			font-size: 7.5pt;
			font-weight: 500;
			line-height: 1.2;
			color: #222222;
			margin-top: 1.5mm;
			white-space: nowrap;
			overflow: hidden;
			text-overflow: ellipsis;
		}}
	</style>
</head>
<body>
<div class="no-print print-bar">
	<div class="print-bar-header">
		<span style="font-weight: 700; font-size: 14px; color: #111827;">Tracora Label Preview {count_suffix}</span>
		<button class="print-btn" onclick="window.print()">🖨️ Print Labels</button>
	</div>
	<div class="print-tips">
		<strong>Thermal Printer Settings:</strong> Set <em>Margins: None</em> and <em>uncheck Headers and footers</em> under More settings.<br>
		<strong>Save to PDF:</strong> Choose Destination <em>Save as PDF</em> to export an exact 50×25mm PDF sticker.
	</div>
</div>
{body_labels}
</body>
</html>
"""


@frappe.whitelist()
def get_label_preview(asset: str) -> dict:
	"""Read-only method to fetch label preview for dialogs without mutating state or recording movements."""
	if not asset or not isinstance(asset, str):
		frappe.throw(_("Asset name must be specified."), frappe.ValidationError)

	if not frappe.has_permission("Tracora Asset", "read", doc=asset):
		frappe.throw(_("Not permitted to view asset {0}.").format(asset), frappe.PermissionError)

	doc = frappe.get_doc("Tracora Asset", asset)
	tag = (doc.asset_tag or doc.name or "").strip()
	if not tag:
		frappe.throw(_("Asset '{0}' does not have an asset tag.").format(asset), frappe.ValidationError)

	width_mm, height_mm, qr_size_mm = _get_label_settings()
	qr_code = qr_base64(tag)

	label_data = {
		"name": doc.name,
		"asset_tag": tag,
		"asset_name": doc.asset_name or "",
		"brand": doc.brand or "",
		"qr_code": qr_code,
		"label_width_mm": width_mm,
		"label_height_mm": height_mm,
		"qr_size_mm": qr_size_mm,
	}
	label_data["preview_html"] = _render_single_label_body(label_data, width_mm, height_mm, qr_size_mm)
	return label_data


@frappe.whitelist()
def print_labels(assets) -> dict:
	"""Mutating print action: validates assets, updates label_printed_on, records Label Reprint movements,
	and returns structured data plus combined printable HTML.
	"""
	if isinstance(assets, str):
		try:
			parsed = json.loads(assets)
			asset_names = parsed if isinstance(parsed, list) else [assets]
		except (ValueError, TypeError):
			asset_names = [assets]
	elif isinstance(assets, list):
		asset_names = assets
	else:
		frappe.throw(_("Invalid assets argument provided."), frappe.ValidationError)

	# Clean asset names and eliminate duplicates while preserving order
	clean_names = []
	for a in asset_names:
		if a and isinstance(a, str):
			item = a.strip()
			if item and item not in clean_names:
				clean_names.append(item)

	if not clean_names:
		frappe.throw(_("Please select at least one asset to print labels."), frappe.ValidationError)

	# Permission validation
	if not frappe.has_permission("Tracora Asset Movement", "create"):
		frappe.throw(_("Not permitted to record asset movements."), frappe.PermissionError)

	for name in clean_names:
		if not frappe.has_permission("Tracora Asset", "write", doc=name):
			frappe.throw(
				_("Not permitted to print labels for asset '{0}' (write permission required).").format(name),
				frappe.PermissionError
			)

	# Phase 1: Upfront validation pass across ALL assets before any DB write
	asset_docs = []
	for name in clean_names:
		if not frappe.db.exists("Tracora Asset", name):
			frappe.throw(_("Asset '{0}' does not exist.").format(name), frappe.ValidationError)
		doc = frappe.get_doc("Tracora Asset", name)
		tag = (doc.asset_tag or doc.name or "").strip()
		if not tag:
			frappe.throw(_("Asset '{0}' does not have a valid asset tag (FR-44).").format(name), frappe.ValidationError)
		asset_docs.append((doc, tag))

	# Phase 2: Atomic execution pass
	width_mm, height_mm, qr_size_mm = _get_label_settings()
	labels_data = []
	now_ts = now_datetime()

	for doc, tag in asset_docs:
		qr_code = qr_base64(tag)
		was_printed = bool(doc.label_printed_on)

		# 1. Update label_printed_on timestamp
		frappe.db.set_value("Tracora Asset", doc.name, "label_printed_on", now_ts, update_modified=True)

		# 2. Append-only Label Reprint movement
		movement = frappe.get_doc({
			"doctype": "Tracora Asset Movement",
			"asset": doc.name,
			"movement_type": "Label Reprint",
			"movement_date": now_ts,
			"recorded_by": frappe.session.user,
			"remarks": "Label reprinted" if was_printed else "Label printed"
		})
		movement.insert(ignore_permissions=True)

		labels_data.append({
			"name": doc.name,
			"asset_tag": tag,
			"asset_name": doc.asset_name or "",
			"brand": doc.brand or "",
			"qr_code": qr_code,
			"label_width_mm": width_mm,
			"label_height_mm": height_mm,
			"qr_size_mm": qr_size_mm,
		})

	combined_html = render_combined_html(labels_data, width_mm, height_mm, qr_size_mm)

	return {
		"labels": labels_data,
		"html": combined_html,
		"count": len(labels_data)
	}
