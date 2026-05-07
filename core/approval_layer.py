import logging
from datetime import datetime, timezone

from memory.memory_store import MemoryStore
from memory.pattern_schema import UXPattern

logger = logging.getLogger(__name__)

APPROVAL_TRIGGERS = {"save this", "approve", "yes save", "keep this", "looks good save"}


def is_approval_message(text: str) -> bool:
    """Check if a user message is an approval for saving the pending pattern."""
    normalized = text.lower().strip().rstrip(".")
    return normalized in APPROVAL_TRIGGERS or normalized.startswith("/approve")


async def approve_and_save_pattern(
    store: MemoryStore,
    pattern_data: dict,
    user_id: int,
    username: str = "",
) -> UXPattern:
    """
    Validate pattern data, save to memory store, and write YAML to design-memory/.
    Returns the saved UXPattern.
    """
    pattern = UXPattern(
        name=pattern_data.get("name", "Unnamed Pattern"),
        category=pattern_data.get("category", "unknown"),
        description=pattern_data.get("description", ""),
        context=pattern_data.get("context", ""),
        anti_pattern_if=pattern_data.get("anti_pattern_if", ""),
        tags=pattern_data.get("tags", []),
        approved_by=f"@{username}" if username else f"user:{user_id}",
        approved_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )

    store.save_pattern(pattern)
    logger.info(f"Saved pattern: {pattern.pattern_id} — {pattern.name}")
    return pattern
