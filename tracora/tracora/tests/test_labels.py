# Copyright (c) 2026, Kishore and Contributors
# See license.txt

import base64
import io
from PIL import Image
import frappe
from frappe.tests.utils import FrappeTestCase
from tracora.tags.qr import qr_base64
from tracora.api.labels import get_label_preview, print_labels


class TestTracoraLabels(FrappeTestCase):
	def setUp(self):
		super().setUp()
		# Base internal company
		if not frappe.db.exists("Tracora Company", "Test Label Corp"):
			frappe.get_doc({
				"doctype": "Tracora Company",
				"company_name": "Test Label Corp",
				"company_type": "Internal",
				"company_abbr": "TLC",
				"company_address": "100 Label St, Chennai",
				"source": "Tracora"
			}).insert()

		# Base branch
		if not frappe.db.exists("Tracora Branch", "HQ - TLC"):
			frappe.get_doc({
				"doctype": "Tracora Branch",
				"branch_name": "HQ",
				"company": "Test Label Corp",
				"source": "Tracora"
			}).insert()

		# Base location
		if not frappe.db.exists("Tracora Location", "HQ Main Store"):
			frappe.get_doc({
				"doctype": "Tracora Location",
				"location_name": "HQ Main Store",
				"address": "Floor 1, HQ Building, Chennai",
				"latitude": 13.0827,
				"longitude": 80.2707,
				"source": "Tracora"
			}).insert()

		# Set standard label dimensions in Settings
		frappe.db.set_single_value("Tracora Settings", "label_width_mm", 50.0)
		frappe.db.set_single_value("Tracora Settings", "label_height_mm", 25.0)
		frappe.db.set_single_value("Tracora Settings", "qr_size_mm", 15.0)

	def tearDown(self):
		super().tearDown()
		# Reset default settings
		frappe.db.set_single_value("Tracora Settings", "label_width_mm", 50.0)
		frappe.db.set_single_value("Tracora Settings", "label_height_mm", 25.0)
		frappe.db.set_single_value("Tracora Settings", "qr_size_mm", 15.0)

	def _create_test_asset(self, tag_mode="Auto-generated", manual_tag=None, asset_name="Test ThinkPad T14"):
		asset_doc = {
			"doctype": "Tracora Asset",
			"tag_mode": tag_mode,
			"asset_name": asset_name,
			"brand": "Lenovo",
			"serial_no": f"SN-{frappe.generate_hash(length=8).upper()}",
			"owner_company": "Test Label Corp",
			"holding_company": "Test Label Corp",
			"branch": "HQ - TLC",
			"location": "HQ Main Store",
			"status": "In Store"
		}
		if tag_mode == "Manual entry":
			asset_doc["asset_tag"] = manual_tag
		doc = frappe.get_doc(asset_doc)
		doc.insert()
		return doc

	def test_fr44_qr_encodes_bare_tag_only(self):
		"""FR-44: QR code encodes strictly the bare tag string — no URL, personal data, or metadata."""
		tag = "TRC-000942"
		data_uri = qr_base64(tag)
		self.assertTrue(data_uri.startswith("data:image/png;base64,"))

		# Verify base64 decode produces a valid PNG image
		raw_b64 = data_uri.replace("data:image/png;base64,", "")
		image_bytes = base64.b64decode(raw_b64)
		img = Image.open(io.BytesIO(image_bytes))
		self.assertEqual(img.format, "PNG")
		self.assertGreaterEqual(img.width, 100)
		self.assertGreaterEqual(img.height, 100)

		# Reject URLs, JSON objects, line breaks, or empty tags
		with self.assertRaises(ValueError):
			qr_base64("https://portal.example.com/asset/TRC-000942")

		with self.assertRaises(ValueError):
			qr_base64("http://scan.tracora/tag")

		with self.assertRaises(ValueError):
			qr_base64('{"asset_tag": "TRC-000942"}')

		with self.assertRaises(ValueError):
			qr_base64("TRC-000942\nUser: Priya")

		with self.assertRaises(ValueError):
			qr_base64("   ")

	def test_fr43_manual_tag_reserved_prefix_refused(self):
		"""FR-43: Typing a manual tag starting with the reserved prefix is refused."""
		with self.assertRaises(frappe.ValidationError) as ctx:
			self._create_test_asset(tag_mode="Manual entry", manual_tag="TRC-999888")
		self.assertIn("reserved prefix", str(ctx.exception).lower())

	def test_read_only_preview_does_not_mutate_state(self):
		"""Review Remark 2: get_label_preview must be purely read-only (no movement records, no timestamp changes)."""
		asset = self._create_test_asset()
		self.assertIsNone(asset.label_printed_on)

		# Initial movement count
		initial_movements = frappe.db.count("Tracora Asset Movement", {"asset": asset.name})

		# Request preview
		preview = get_label_preview(asset.name)
		self.assertEqual(preview["name"], asset.name)
		self.assertEqual(preview["asset_tag"], asset.asset_tag)
		self.assertTrue(preview["qr_code"].startswith("data:image/png;base64,"))
		self.assertEqual(preview["label_width_mm"], 50.0)
		self.assertEqual(preview["label_height_mm"], 25.0)
		self.assertEqual(preview["qr_size_mm"], 15.0)
		self.assertIn("label-page", preview["preview_html"])

		# Reload asset: verify NO timestamp or movements were created
		reloaded = frappe.get_doc("Tracora Asset", asset.name)
		self.assertIsNone(reloaded.label_printed_on)
		after_movements = frappe.db.count("Tracora Asset Movement", {"asset": asset.name})
		self.assertEqual(initial_movements, after_movements)

	def test_batch_printing_upfront_validation(self):
		"""Review Remark 3: Upfront validation fails before writing if any asset in batch is invalid."""
		asset1 = self._create_test_asset()
		initial_printed_on = asset1.label_printed_on

		# Run batch with 1 valid asset and 1 non-existent asset
		with self.assertRaises(frappe.ValidationError):
			print_labels([asset1.name, "NON-EXISTENT-ASSET-ID"])

		# Assert asset1 was NOT stamped and no movement was recorded
		reloaded = frappe.get_doc("Tracora Asset", asset1.name)
		self.assertEqual(reloaded.label_printed_on, initial_printed_on)
		movements = frappe.db.count("Tracora Asset Movement", {"asset": asset1.name, "movement_type": "Label Reprint"})
		self.assertEqual(movements, 0)

	def test_fr47_batch_printing_combined_document(self):
		"""FR-47: Batch printing creates 1 combined document for multiple assets and stamps all."""
		asset1 = self._create_test_asset(asset_name="Dell Latitude 5420")
		asset2 = self._create_test_asset(asset_name="MacBook Pro 16")
		asset3 = self._create_test_asset(asset_name="ThinkCentre M70q")

		res = print_labels([asset1.name, asset2.name, asset3.name])
		self.assertEqual(res["count"], 3)
		self.assertEqual(len(res["labels"]), 3)

		# Verify combined HTML output
		html = res["html"]
		self.assertIn(asset1.asset_tag, html)
		self.assertIn(asset2.asset_tag, html)
		self.assertIn(asset3.asset_tag, html)
		self.assertIn("50.0mm 25.0mm", html)
		self.assertIn("page-break-after: always", html)

		# Verify each asset has label_printed_on stamped and a Label Reprint movement
		for a in [asset1, asset2, asset3]:
			doc = frappe.get_doc("Tracora Asset", a.name)
			self.assertIsNotNone(doc.label_printed_on)

			mv = frappe.get_all(
				"Tracora Asset Movement",
				filters={"asset": a.name, "movement_type": "Label Reprint"},
				fields=["name", "remarks"]
			)
			self.assertEqual(len(mv), 1)
			self.assertEqual(mv[0].remarks, "Label printed")

	def test_fr48_reprint_twice(self):
		"""FR-48: Reprinting twice leaves tag unchanged, creates two Label Reprint movements."""
		asset = self._create_test_asset()
		original_tag = asset.asset_tag

		# 1st Print
		res1 = print_labels([asset.name])
		self.assertEqual(res1["count"], 1)

		doc_after_1 = frappe.get_doc("Tracora Asset", asset.name)
		self.assertEqual(doc_after_1.asset_tag, original_tag)
		self.assertIsNotNone(doc_after_1.label_printed_on)

		mv1 = frappe.get_all(
			"Tracora Asset Movement",
			filters={"asset": asset.name, "movement_type": "Label Reprint"},
			fields=["name", "remarks", "movement_date"],
			order_by="creation asc"
		)
		self.assertEqual(len(mv1), 1)
		self.assertEqual(mv1[0].remarks, "Label printed")

		# 2nd Print (Reprint)
		res2 = print_labels([asset.name])
		self.assertEqual(res2["count"], 1)

		doc_after_2 = frappe.get_doc("Tracora Asset", asset.name)
		self.assertEqual(doc_after_2.asset_tag, original_tag)

		mv2 = frappe.get_all(
			"Tracora Asset Movement",
			filters={"asset": asset.name, "movement_type": "Label Reprint"},
			fields=["name", "remarks", "movement_date"],
			order_by="creation asc"
		)
		self.assertEqual(len(mv2), 2)
		self.assertEqual(mv2[1].remarks, "Label reprinted")

	def test_settings_dimensions_reflected(self):
		"""Label and QR dimensions in output dynamically inherit Tracora Settings."""
		frappe.db.set_single_value("Tracora Settings", "label_width_mm", 60.0)
		frappe.db.set_single_value("Tracora Settings", "label_height_mm", 30.0)
		frappe.db.set_single_value("Tracora Settings", "qr_size_mm", 18.0)

		asset = self._create_test_asset()
		preview = get_label_preview(asset.name)
		self.assertEqual(preview["label_width_mm"], 60.0)
		self.assertEqual(preview["label_height_mm"], 30.0)
		self.assertEqual(preview["qr_size_mm"], 18.0)
		self.assertIn("width: 18.0mm; height: 18.0mm;", preview["preview_html"])

		res = print_labels([asset.name])
		self.assertIn("60.0mm 30.0mm", res["html"])
		self.assertIn("width: 18.0mm; height: 18.0mm;", res["html"])


	def test_live_qr_scan_decoding_with_zxing(self):
		"""Create a real asset QR code, scan it using ZXing engine, and verify the decoded payload."""
		import json
		import subprocess
		from pathlib import Path

		asset = self._create_test_asset(asset_name="Lenovo ThinkPad X1 Carbon Gen 11")
		tag = asset.asset_tag
		self.assertTrue(tag.startswith("TRC-"))

		# 1. Generate QR code via backend API
		preview = get_label_preview(asset.name)
		data_uri = preview["qr_code"]
		raw_b64 = data_uri.replace("data:image/png;base64,", "")
		png_bytes = base64.b64decode(raw_b64)

		# 2. Save physical PNG artifact
		artifact_dir = Path("/mnt/c/Users/kishore.k_aionioncap/.gemini/antigravity-ide/brain/fffa2261-4c74-450f-9619-1d8bea33326f")
		qr_img_path = artifact_dir / "scanned_asset_qr.png"
		qr_img_path.write_bytes(png_bytes)

		# 3. Convert to grayscale raw buffer
		img = Image.open(io.BytesIO(png_bytes)).convert("L")
		w, h = img.size
		raw_path = Path("/tmp/qr_test_gray.raw")
		raw_path.write_bytes(img.tobytes())

		# 4. Invoke ZXing scanner
		node_script = f"""
		const fs = require('fs');
		const ZXing = require('/home/kishore/frappe-bench/apps/frappe/node_modules/html5-qrcode/third_party/zxing-js.umd.js');

		const buf = fs.readFileSync('{raw_path}');
		const lum = new ZXing.RGBLuminanceSource(new Uint8ClampedArray(buf), {w}, {h});
		const bin = new ZXing.HybridBinarizer(lum);
		const bitmap = new ZXing.BinaryBitmap(bin);
		const reader = new ZXing.QRCodeReader();

		try {{
			const result = reader.decode(bitmap);
			console.log(JSON.stringify({{
				success: true,
				text: result.getText(),
				format: result.getBarcodeFormat()
			}}));
		}} catch (e) {{
			console.log(JSON.stringify({{
				success: false,
				error: e.toString()
			}}));
		}}
		"""

		res = subprocess.run(["node", "-e", node_script], capture_output=True, text=True)
		decode_result = json.loads(res.stdout.strip())
		self.assertTrue(decode_result["success"], f"ZXing decoding failed: {decode_result.get('error')}")

		decoded_text = decode_result["text"]
		barcode_format = decode_result["format"]

		print(f"\n[SCANNER OUTPUT] Format: QR_CODE ({barcode_format}) | Decoded Text: '{decoded_text}' | Expected: '{tag}'")

		# Assert exact bare tag match
		self.assertEqual(decoded_text, tag)
		self.assertNotIn("http", decoded_text)
		self.assertNotIn("{", decoded_text)
