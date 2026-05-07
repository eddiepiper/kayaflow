from __future__ import annotations

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def extract_text(image_bytes: bytes) -> str | None:
    """
    Extract text from a UI screenshot using pytesseract.
    Returns extracted text or None if OCR is unavailable/fails.
    """
    try:
        import pytesseract
    except ImportError:
        logger.debug("pytesseract not installed — OCR disabled")
        return None

    try:
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img, lang="eng")
        cleaned = _clean_ocr_output(text)
        if cleaned:
            logger.debug(f"OCR extracted {len(cleaned)} chars")
        return cleaned or None
    except Exception as e:
        logger.warning(f"OCR extraction failed: {e}")
        return None


def _clean_ocr_output(raw: str) -> str:
    """Remove noise from OCR output — keep lines with actual content."""
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        # Skip very short lines (single chars, noise)
        if len(stripped) < 2:
            continue
        # Skip lines that are purely symbols/numbers with no letters
        if stripped and not any(c.isalpha() for c in stripped):
            continue
        lines.append(stripped)
    return "\n".join(lines)
