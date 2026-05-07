from __future__ import annotations

import base64
import logging

import anthropic

from config.settings import CLAUDE_QUICK_MODEL, JOURNEY_CATEGORIES
from config.prompts import JOURNEY_DETECTION_PROMPT

logger = logging.getLogger(__name__)


async def detect_journey_stage(
    client: anthropic.AsyncAnthropic,
    image_bytes: bytes,
    user_hint: str | None = None,
) -> str:
    """
    Detect the journey stage of a UI screenshot.
    Returns a category from JOURNEY_CATEGORIES or 'unknown'.
    If user_hint is provided and matches a category, use it directly.
    """
    if user_hint:
        normalized = user_hint.lower().replace(" ", "-")
        if normalized in JOURNEY_CATEGORIES:
            logger.debug(f"Using user-provided journey hint: {normalized}")
            return normalized

    try:
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        response = await client.messages.create(
            model=CLAUDE_QUICK_MODEL,
            max_tokens=20,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": JOURNEY_DETECTION_PROMPT},
                    ],
                }
            ],
        )
        detected = response.content[0].text.strip().lower()
        if detected in JOURNEY_CATEGORIES:
            logger.debug(f"Detected journey stage: {detected}")
            return detected
        logger.debug(f"Unrecognized journey stage response: {detected!r}, defaulting to unknown")
        return "unknown"
    except Exception as e:
        logger.warning(f"Journey detection failed: {e}")
        return "unknown"
