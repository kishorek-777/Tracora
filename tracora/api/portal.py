# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import format_datetime, pretty_date, now_datetime


def _derive_category(asset_name, brand, model_number):
	text = f"{asset_name or ''} {brand or ''} {model_number or ''}".lower()
	if any(k in text for k in ["laptop", "macbook", "thinkpad", "latitude", "notebook", "zenbook"]):
		return "Laptops"
	elif any(k in text for k in ["monitor", "display", "screen", "oled", "led"]):
		return "Monitors"
	elif any(k in text for k in ["phone", "iphone", "pixel", "galaxy", "android"]):
		return "Mobile Phones"
	elif any(k in text for k in ["mouse", "keyboard", "headphone", "headset", "adapter", "dock", "dongle", "cable"]):
		return "Accessories"
	elif any(k in text for k in ["desktop", "workstation", "imac", "optiplex", "tower", "server"]):
		return "Desktops"
	elif brand:
		return brand
	return "Hardware"


@frappe.whitelist()
def get_dashboard_summary():
	"""
	Consolidated dashboard summary endpoint for Tracora Asset Intelligence Platform.
	Returns summary metrics, category distribution, location intelligence,
	recent assets, recent movements, and attention alerts in a single payload.
	"""
	# 1. Summary Metrics
	total_assets = frappe.db.count("Tracora Asset") or 0
	assigned_assets = frappe.db.count("Tracora Asset", filters={"status": "In Circulation"}) or 0
	available_assets = frappe.db.count("Tracora Asset", filters={"status": "In Store"}) or 0
	maintenance_assets = frappe.db.count("Tracora Asset", filters={"status": "Under Maintenance"}) or 0
	lost_assets = frappe.db.count("Tracora Asset", filters={"status": "Lost"}) or 0
	damaged_assets = frappe.db.count("Tracora Asset", filters={"condition": ["in", ["Damaged", "Non-Functional"]]}) or 0

	accounted_rate = 100.0
	if total_assets > 0:
		unaccounted = lost_assets
		accounted_rate = round(((total_assets - unaccounted) / total_assets) * 100, 1)

	attention_count = maintenance_assets + damaged_assets + lost_assets

	summary = {
		"total_assets": total_assets,
		"assigned_assets": assigned_assets,
		"available_assets": available_assets,
		"maintenance_assets": maintenance_assets,
		"lost_assets": lost_assets,
		"damaged_assets": damaged_assets,
		"accounted_rate": accounted_rate,
		"attention_count": attention_count,
		"trend_total": "+12%",
		"trend_assigned": "+8%",
		"trend_available": "+5%",
		"trend_maintenance": "-3%"
	}

	# 2. Categories Distribution (Derived from Assets)
	all_assets_for_cat = frappe.get_all(
		"Tracora Asset",
		fields=["asset_name", "brand", "model_number"]
	)

	cat_counts = {}
	for a in all_assets_for_cat:
		cat = _derive_category(a.asset_name, a.brand, a.model_number)
		cat_counts[cat] = cat_counts.get(cat, 0) + 1

	categories = []
	for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
		pct = round((count / total_assets * 100), 1) if total_assets > 0 else 0
		categories.append({
			"category": cat,
			"count": count,
			"percentage": pct
		})

	if not categories:
		categories = [
			{"category": "Laptops", "count": 0, "percentage": 0.0},
			{"category": "Monitors", "count": 0, "percentage": 0.0},
			{"category": "Mobile Phones", "count": 0, "percentage": 0.0},
			{"category": "Accessories", "count": 0, "percentage": 0.0},
			{"category": "Desktops", "count": 0, "percentage": 0.0},
		]

	# 3. Location Intelligence
	locations_raw = frappe.db.sql("""
		SELECT l.name as location, l.location_name, l.latitude, l.longitude, COUNT(a.name) as count
		FROM `tabTracora Location` l
		LEFT JOIN `tabTracora Asset` a ON a.location = l.name
		GROUP BY l.name, l.location_name, l.latitude, l.longitude
		ORDER BY count DESC
		LIMIT 6
	""", as_dict=True)

	locations = []
	for loc in locations_raw:
		locations.append({
			"location": loc.location,
			"name": loc.location_name or loc.location,
			"city": loc.location_name or loc.location,
			"count": loc.count or 0,
			"latitude": loc.latitude,
			"longitude": loc.longitude
		})

	# 4. Recent Assets (8 latest)
	recent_assets_raw = frappe.get_all(
		"Tracora Asset",
		fields=["name", "asset_tag", "asset_name", "brand", "model_number", "serial_no", "assigned_to", "location", "status", "condition", "owner_company", "creation"],
		order_by="creation desc",
		limit=8
	)

	recent_assets = []
	for asset in recent_assets_raw:
		emp_name = None
		if asset.assigned_to:
			emp_name = frappe.db.get_value("Tracora Employee", asset.assigned_to, "employee_name") or asset.assigned_to

		loc_name = None
		if asset.location:
			loc_name = frappe.db.get_value("Tracora Location", asset.location, "location_name") or asset.location

		cat = _derive_category(asset.asset_name, asset.brand, asset.model_number)

		recent_assets.append({
			"name": asset.name,
			"asset_tag": asset.asset_tag or asset.name,
			"asset_name": asset.asset_name,
			"brand": asset.brand or "",
			"model_number": asset.model_number or "",
			"category": cat,
			"serial_no": asset.serial_no or "—",
			"assigned_to": asset.assigned_to,
			"assigned_to_name": emp_name or "Unassigned",
			"location": loc_name or asset.location or "HQ Storage",
			"status": asset.status or "In Store",
			"condition": asset.condition or "New",
			"owner_company": asset.owner_company or "Aionion Capital",
			"created_time_ago": pretty_date(asset.creation)
		})

	# 5. Recent Movements (Timeline Feed)
	movements_raw = frappe.get_all(
		"Tracora Asset Movement",
		fields=["name", "asset", "movement_type", "from_employee", "to_employee", "from_status", "to_status", "from_location", "to_location", "recorded_by", "remarks", "creation"],
		order_by="creation desc",
		limit=8
	)

	recent_movements = []
	for m in movements_raw:
		asset_tag = frappe.db.get_value("Tracora Asset", m.asset, "asset_tag") or m.asset
		asset_name = frappe.db.get_value("Tracora Asset", m.asset, "asset_name") or ""
		to_emp = frappe.db.get_value("Tracora Employee", m.to_employee, "employee_name") if m.to_employee else None
		from_emp = frappe.db.get_value("Tracora Employee", m.from_employee, "employee_name") if m.from_employee else None
		recorder = frappe.db.get_value("User", m.recorded_by, "full_name") if m.recorded_by else m.recorded_by
		loc = m.to_location or m.from_location or "Main Facility"
		loc_name = frappe.db.get_value("Tracora Location", loc, "location_name") if loc else loc

		recent_movements.append({
			"name": m.name,
			"asset": m.asset,
			"asset_tag": asset_tag,
			"asset_name": asset_name,
			"movement_type": m.movement_type,
			"to_employee": m.to_employee,
			"to_employee_name": to_emp or m.to_employee,
			"from_employee": m.from_employee,
			"from_employee_name": from_emp or m.from_employee,
			"recorded_by_name": recorder or "System",
			"location": loc_name or loc or "Main Facility",
			"remarks": m.remarks or "",
			"creation": str(m.creation),
			"time_ago": pretty_date(m.creation)
		})

	# 6. Actionable Alerts
	alerts = []
	if maintenance_assets > 0:
		alerts.append({
			"type": "warning",
			"title": _("Assets in Maintenance"),
			"message": _("{0} asset(s) currently undergoing repair or maintenance").format(maintenance_assets),
			"count": maintenance_assets
		})
	if lost_assets > 0:
		alerts.append({
			"type": "danger",
			"title": _("Reported Lost Assets"),
			"message": _("{0} asset(s) flagged as lost and require audit review").format(lost_assets),
			"count": lost_assets
		})
	if damaged_assets > 0:
		alerts.append({
			"type": "attention",
			"title": _("Damaged Hardware"),
			"message": _("{0} asset(s) reported in damaged condition").format(damaged_assets),
			"count": damaged_assets
		})

	return {
		"summary": summary,
		"categories": categories,
		"locations": locations,
		"recent_assets": recent_assets,
		"recent_movements": recent_movements,
		"alerts": alerts,
		"system_status": {
			"status": "Online",
			"version": "2.0.0",
			"sync": "Active",
			"server_time": format_datetime(now_datetime(), "dd MMM yyyy HH:mm:ss")
		}
	}


@frappe.whitelist()
def scan_asset(code):
	"""
	First-class barcode/QR code resolution endpoint.
	Looks up an asset by serial_no, asset_tag, or name.
	"""
	if not code:
		frappe.throw(_("Scan query or asset ID is required"))

	code = code.strip()

	asset = frappe.db.get_value(
		"Tracora Asset",
		{"name": code},
		["name", "asset_tag", "asset_name", "brand", "model_number", "serial_no", "assigned_to", "location", "status", "condition", "owner_company", "creation"],
		as_dict=True
	)

	if not asset:
		asset = frappe.db.get_value(
			"Tracora Asset",
			{"asset_tag": code},
			["name", "asset_tag", "asset_name", "brand", "model_number", "serial_no", "assigned_to", "location", "status", "condition", "owner_company", "creation"],
			as_dict=True
		)

	if not asset:
		asset = frappe.db.get_value(
			"Tracora Asset",
			{"serial_no": code},
			["name", "asset_tag", "asset_name", "brand", "model_number", "serial_no", "assigned_to", "location", "status", "condition", "owner_company", "creation"],
			as_dict=True
		)

	if not asset:
		frappe.throw(_("No asset found matching '{0}'").format(code), frappe.DoesNotExistError)

	holder_info = None
	if asset.assigned_to:
		holder = frappe.db.get_value(
			"Tracora Employee",
			asset.assigned_to,
			["employee_name", "company", "department", "status"],
			as_dict=True
		)
		if holder:
			holder_info = {
				"employee_id": asset.assigned_to,
				"employee_name": holder.employee_name,
				"company": holder.company,
				"department": holder.department,
				"status": holder.status
			}

	movements = frappe.get_all(
		"Tracora Asset Movement",
		filters={"asset": asset.name},
		fields=["name", "movement_type", "from_employee", "to_employee", "from_location", "to_location", "recorded_by", "remarks", "creation"],
		order_by="creation desc",
		limit=5
	)

	movement_trail = []
	for m in movements:
		to_emp = frappe.db.get_value("Tracora Employee", m.to_employee, "employee_name") if m.to_employee else None
		recorder = frappe.db.get_value("User", m.recorded_by, "full_name") if m.recorded_by else m.recorded_by
		loc = m.to_location or m.from_location
		movement_trail.append({
			"movement_type": m.movement_type,
			"to_employee": m.to_employee,
			"to_employee_name": to_emp or m.to_employee,
			"location": loc,
			"recorded_by": recorder or m.recorded_by,
			"remarks": m.remarks,
			"time_ago": pretty_date(m.creation)
		})

	asset["category"] = _derive_category(asset.get("asset_name"), asset.get("brand"), asset.get("model_number"))

	return {
		"asset": asset,
		"holder": holder_info,
		"movement_trail": movement_trail
	}


@frappe.whitelist()
def search_assets(query):
	"""
	Command bar search endpoint (Cmd+K) returning matched assets, employees, and locations.
	"""
	if not query or len(query.strip()) < 1:
		return {"assets": [], "employees": [], "locations": []}

	q = f"%{query.strip()}%"

	assets = frappe.db.sql("""
		SELECT name, asset_tag, asset_name, brand, model_number, serial_no, status, assigned_to, location
		FROM `tabTracora Asset`
		WHERE name LIKE %s OR asset_tag LIKE %s OR serial_no LIKE %s OR asset_name LIKE %s OR brand LIKE %s
		LIMIT 6
	""", (q, q, q, q, q), as_dict=True)

	employees = frappe.db.sql("""
		SELECT name, employee_name, company, department, status
		FROM `tabTracora Employee`
		WHERE name LIKE %s OR employee_name LIKE %s
		LIMIT 5
	""", (q, q), as_dict=True)

	locations = frappe.db.sql("""
		SELECT name, location_name
		FROM `tabTracora Location`
		WHERE name LIKE %s OR location_name LIKE %s OR address LIKE %s
		LIMIT 4
	""", (q, q, q), as_dict=True)

	return {
		"assets": assets,
		"employees": employees,
		"locations": locations
	}
