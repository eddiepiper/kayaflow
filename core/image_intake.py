import io
import logging
from pathlib import Path

from PIL import Image
from telegram import PhotoSize, Bot

logger = logging.getLogger(__name__)

MAX_IMAGE_DIMENSION = 2048


async def download_telegram_photo(bot: Bot, photo: PhotoSize) -> bytes:
    """Download the highest-quality version of a Telegram photo."""
    file = await bot.get_file(photo.file_id)
    buf = io.BytesIO()
    await file.download_to_memory(buf)
    buf.seek(0)
    return buf.read()


def preprocess_image(image_bytes: bytes) -> tuple[bytes, dict]:
    """
    Resize and normalize image for Claude vision.
    Returns (processed_bytes, metadata).
    """
    img = Image.open(io.BytesIO(image_bytes))
    metadata = {
        "original_size": img.size,
        "mode": img.mode,
        "format": img.format,
    }

    # Convert to RGB if needed (handles RGBA, palette mode, etc.)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Resize if too large (Claude handles up to 1568px on longest side)
    width, height = img.size
    if max(width, height) > MAX_IMAGE_DIMENSION:
        ratio = MAX_IMAGE_DIMENSION / max(width, height)
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        metadata["resized_to"] = img.size
        logger.debug(f"Resized image from {metadata['original_size']} to {img.size}")

    # Re-encode as JPEG for consistency
    out_buf = io.BytesIO()
    img.save(out_buf, format="JPEG", quality=90, optimize=True)
    out_buf.seek(0)
    return out_buf.read(), metadata


def get_best_photo(photos: list[PhotoSize]) -> PhotoSize:
    """Select the highest-resolution photo from a Telegram photo array."""
    return max(photos, key=lambda p: p.width * p.height)
