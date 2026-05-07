"""
Hermes-style memory: retrieve relevant patterns to augment UX critique context.
"Hermes" = messenger that brings past knowledge into current conversation.
"""
from __future__ import annotations

import logging

from memory.memory_store import MemoryStore
from memory.pattern_schema import UXPattern

logger = logging.getLogger(__name__)

MAX_PATTERNS_IN_CONTEXT = 3


def retrieve_relevant_patterns(
    store: MemoryStore,
    journey_stage: str,
    tags: list[str] | None = None,
) -> list[UXPattern]:
    """
    Retrieve patterns relevant to the current review context.
    Prioritizes category match, then tag overlap.
    """
    candidates = []

    # Primary: same category
    if journey_stage and journey_stage != "unknown":
        candidates = store.get_patterns_by_category(journey_stage)

    # Secondary: tag overlap (if we have tags and not enough candidates)
    if len(candidates) < MAX_PATTERNS_IN_CONTEXT and tags:
        all_patterns = store.get_all_patterns()
        for pattern in all_patterns:
            if pattern in candidates:
                continue
            if any(t in pattern.tags for t in tags):
                candidates.append(pattern)

    return candidates[:MAX_PATTERNS_IN_CONTEXT]


def format_memory_context(patterns: list[UXPattern]) -> str:
    """Format patterns as a concise context block for the critique prompt."""
    if not patterns:
        return ""

    lines = []
    for p in patterns:
        lines.append(f"**{p.name}** ({p.category})")
        lines.append(f"  {p.description}")
        if p.context:
            lines.append(f"  When to use: {p.context}")
        if p.anti_pattern_if:
            lines.append(f"  Anti-pattern if: {p.anti_pattern_if}")
        lines.append("")

    return "\n".join(lines).strip()


def build_memory_context(
    store: MemoryStore,
    journey_stage: str,
    tags: list[str] | None = None,
) -> str:
    """
    Full pipeline: retrieve relevant patterns and format as context string.
    Returns empty string if no relevant patterns found.
    """
    if store.count() == 0:
        return ""

    patterns = retrieve_relevant_patterns(store, journey_stage, tags)
    if not patterns:
        logger.debug("No relevant patterns found for memory context")
        return ""

    context = format_memory_context(patterns)
    logger.debug(f"Memory context built from {len(patterns)} patterns")
    return context
