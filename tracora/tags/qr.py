# Copyright (c) 2026, Kishore and contributors
# For license information, please see license.txt

import base64
import io
import qrcode
from qrcode.constants import ERROR_CORRECT_M


def qr_base64(tag: str) -> str:
	"""Generate a base64-encoded PNG data URI for a QR code encoding ONLY the bare tag string.
	
	Per FR-44 & Rule 8: No URL, no employee, no company, no personal data, ever.
	"""
	if not tag or not isinstance(tag, str) or not tag.strip():
		raise ValueError("Tag must be a non-empty string.")

	clean_tag = tag.strip()

	# Safety checks: ensure it is strictly a bare tag identifier, never a URL or JSON object
	lowered = clean_tag.lower()
	if lowered.startswith("http://") or lowered.startswith("https://"):
		raise ValueError("QR code payload must be a bare tag string, not a URL.")
	if clean_tag.startswith("{") and clean_tag.endswith("}"):
		raise ValueError("QR code payload must be a bare tag string, not JSON metadata.")
	if "\n" in clean_tag or "\r" in clean_tag:
		raise ValueError("QR code payload cannot contain line breaks.")

	qr = qrcode.QRCode(
		version=None,
		error_correction=ERROR_CORRECT_M,
		box_size=10,
		border=2,  # Intact quiet zone
	)
	qr.add_data(clean_tag)
	qr.make(fit=True)

	img = qr.make_image(fill_color="black", back_color="white")
	buf = io.BytesIO()
	img.save(buf, format="PNG")
	raw_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
	return f"data:image/png;base64,{raw_b64}"
