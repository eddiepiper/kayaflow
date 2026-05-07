"""
Seed the design memory with example patterns for development and demos.
Run: python scripts/seed_memory.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.memory_store import MemoryStore
from memory.pattern_schema import UXPattern

SEED_PATTERNS = [
    UXPattern(
        pattern_id="seed-001",
        name="Progressive Disclosure Onboarding",
        category="onboarding",
        description="Show only essential fields first; reveal additional fields progressively as user completes each step.",
        context="Use when the full form is long (>5 fields) or when user trust is still being established.",
        anti_pattern_if="All fields shown at once — overwhelming for new users, increases drop-off.",
        tags=["onboarding", "progressive", "form", "low-friction"],
        approved_by="@seed",
        approved_at="2026-05-07",
    ),
    UXPattern(
        pattern_id="seed-002",
        name="Social Proof Above the Fold",
        category="trust-signals",
        description="Place user count, ratings, or partner logos in the first visible screen area, before any CTA.",
        context="Critical for fintech and new products where users are risk-averse.",
        anti_pattern_if="Social proof buried below the fold or absent entirely on high-stakes screens.",
        tags=["trust", "social-proof", "above-fold", "fintech"],
        approved_by="@seed",
        approved_at="2026-05-07",
    ),
    UXPattern(
        pattern_id="seed-003",
        name="Single Primary CTA Per Screen",
        category="cta-patterns",
        description="One prominent primary action button per screen, with secondary actions visually de-emphasized.",
        context="Reduces decision paralysis; especially important on conversion-critical screens.",
        anti_pattern_if="Multiple equal-weight buttons competing for attention on same screen.",
        tags=["cta", "conversion", "focus", "button"],
        approved_by="@seed",
        approved_at="2026-05-07",
    ),
    UXPattern(
        pattern_id="seed-004",
        name="Document Upload with Live Preview",
        category="kyc",
        description="Show a real-time preview of the uploaded document with clear crop/quality indicators before submission.",
        context="Reduces rejection rates by letting users self-correct poor quality scans before submit.",
        anti_pattern_if="Upload with no preview — user doesn't know if image quality is acceptable.",
        tags=["kyc", "document-upload", "feedback", "preview"],
        approved_by="@seed",
        approved_at="2026-05-07",
    ),
    UXPattern(
        pattern_id="seed-005",
        name="Persistent Back Navigation",
        category="navigation",
        description="Always show a visible back/close button on modal and deep screens; never trap users.",
        context="Critical on mobile; users need confidence they can exit any flow.",
        anti_pattern_if="No back button on deep screens — users feel trapped and abandon.",
        tags=["navigation", "back", "mobile", "escape-hatch"],
        approved_by="@seed",
        approved_at="2026-05-07",
    ),
]


def main() -> None:
    store = MemoryStore()
    existing = store.count()

    seeded = 0
    for pattern in SEED_PATTERNS:
        # Don't overwrite existing non-seed patterns
        store.save_pattern(pattern)
        seeded += 1
        print(f"  ✓ {pattern.name} ({pattern.category})")

    print(f"\nSeeded {seeded} patterns. Total in store: {store.count()} (was {existing})")


if __name__ == "__main__":
    main()
