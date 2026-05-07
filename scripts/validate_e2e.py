"""
KayaFlow V1 — CLI End-to-End Validation
Exercises the full pipeline without Telegram or live API keys.
Claude is stubbed with realistic fixture responses.
"""
from __future__ import annotations

import asyncio
import io
import pathlib
import sys
import tempfile
from unittest.mock import AsyncMock, MagicMock

# --- project root on path ---
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.image_intake import preprocess_image
from core.ocr_extractor import extract_text
from core.journey_context import detect_journey_stage
from core.ux_critique_engine import critique_screenshot, _extract_pattern
from core.conversation_manager import ConversationManager
from core.approval_layer import is_approval_message, approve_and_save_pattern
from memory.hermes_memory import build_memory_context
from memory.memory_store import MemoryStore
from memory.pattern_schema import UXPattern


# ── helpers ──────────────────────────────────────────────────────────────────

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
HEAD = "\033[1m"
RESET = "\033[0m"

results: list[tuple[str, bool, str]] = []


def step(label: str, ok: bool, detail: str = "") -> None:
    symbol = PASS if ok else FAIL
    print(f"  {symbol} {label}" + (f"  →  {detail}" if detail else ""))
    results.append((label, ok, detail))
    if not ok:
        print(f"      {FAIL} FATAL: stopping validation")
        _summary()
        sys.exit(1)


def _summary() -> None:
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{'─'*54}")
    print(f"  {HEAD}Results: {passed} passed, {failed} failed{RESET}")
    print(f"{'─'*54}\n")


# ── synthetic test image (generated via Pillow — guaranteed valid) ────────────

def _make_test_jpeg() -> bytes:
    """Generate a 100×100 RGB JPEG simulating a UI mockup screenshot."""
    from PIL import Image as _Image, ImageDraw as _ImageDraw
    img = _Image.new("RGB", (100, 100), color=(240, 240, 245))
    draw = _ImageDraw.Draw(img)
    # Draw a fake "button" rectangle
    draw.rectangle([20, 70, 80, 90], fill=(65, 105, 225))
    # Draw a fake "form field"
    draw.rectangle([10, 30, 90, 50], outline=(180, 180, 180), fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    return buf.read()

MINIMAL_JPEG = _make_test_jpeg()

# Stub Claude response text — simulates what the real model would return
STUB_CRITIQUE = """\
First impression: Clean layout but the CTA is buried below the fold lah.

What's working:
• Logo placement is clear and brand-consistent
• Progress indicator at the top gives users a sense of how long this takes

Main issues:
1. Primary CTA button blends into the background — contrast ratio looks below 4.5:1
2. "Skip for now" text link competes visually with the main action, confusing priority
3. No trust signal near the form — users hesitant to submit personal info without one

Try this:
• Change CTA background to your primary brand colour with white text
• Move "Skip for now" below the CTA, styled as a plain text link not a button

What's the main drop-off point you're seeing in your onboarding funnel right now?\
"""

STUB_PATTERN_JSON = """\
{
  "found_pattern": true,
  "pattern": {
    "name": "Single High-Contrast CTA",
    "category": "cta-patterns",
    "description": "One primary CTA button with brand colour fill and white text, minimum 4.5:1 contrast ratio.",
    "context": "Use on any conversion screen where a single next action should be unambiguous.",
    "anti_pattern_if": "Multiple equal-weight buttons competing on the same screen.",
    "tags": ["cta", "contrast", "accessibility", "conversion"]
  }
}
"""

STUB_JOURNEY = "onboarding"


def make_stub_client(
    responses: list[str],
) -> MagicMock:
    """
    Build a mock AsyncAnthropic client that returns responses in order.
    Each call pops the next response from the list; last item repeats if exhausted.
    """
    client = MagicMock()
    _responses = list(responses)

    async def create(**kwargs):
        text = _responses.pop(0) if len(_responses) > 1 else _responses[0]
        response = MagicMock()
        response.content = [MagicMock(text=text)]
        return response

    client.messages.create = create
    return client


# ── main validation flow ──────────────────────────────────────────────────────

async def run() -> None:
    print(f"\n{'─'*54}")
    print(f"  {HEAD}KayaFlow V1 — CLI End-to-End Validation{RESET}")
    print(f"  Telegram: NOT USED  |  Claude: STUBBED")
    print(f"{'─'*54}\n")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        store = MemoryStore(
            store_path=tmp_path / "store.json",
            design_memory_path=tmp_path / "design-memory",
        )
        conv = ConversationManager()
        # critique_screenshot makes 2 calls: 1=critique, 2=pattern extraction
        client = make_stub_client([STUB_CRITIQUE, STUB_PATTERN_JSON])
        # journey detection makes its own single call
        journey_client = make_stub_client([STUB_JOURNEY])
        user_id = 42

        # ── Step 1: Simulate UI screenshot input ─────────────────────────────
        print(f"  {HEAD}Step 1 — Simulate UI screenshot input{RESET}")
        raw_bytes = MINIMAL_JPEG
        step("Raw image bytes received", len(raw_bytes) > 0, f"{len(raw_bytes)} bytes")

        # ── Step 2: Image preprocessing + OCR stub ───────────────────────────
        print(f"\n  {HEAD}Step 2 — Image preprocessing + OCR{RESET}")
        processed_bytes, metadata = preprocess_image(raw_bytes)
        step("Image preprocessed", len(processed_bytes) > 0,
             f"size={metadata['original_size']}")

        ocr_text = extract_text(processed_bytes)
        step("OCR ran without crash", True,
             "text=None (pytesseract not installed — graceful fallback)")
        step("OCR result is None or str",
             ocr_text is None or isinstance(ocr_text, str),
             repr(ocr_text))

        # ── Step 3: Journey context detection ────────────────────────────────
        print(f"\n  {HEAD}Step 3 — Journey context detection{RESET}")
        detected_stage = await detect_journey_stage(journey_client, processed_bytes)
        step("Journey stage detected", detected_stage == "onboarding",
             f"stage='{detected_stage}'")
        conv.set_journey_stage(user_id, detected_stage)

        # ── Step 4: Memory context (empty store — should return empty string) ─
        print(f"\n  {HEAD}Step 4 — Hermes memory retrieval{RESET}")
        memory_ctx = build_memory_context(store, detected_stage)
        step("Memory context empty on fresh store", memory_ctx == "",
             f"len={len(memory_ctx)}")

        # ── Step 5: UX critique engine ────────────────────────────────────────
        print(f"\n  {HEAD}Step 5 — UX critique engine{RESET}")
        feedback, pattern_candidate = await critique_screenshot(
            client=client,
            image_bytes=processed_bytes,
            journey_stage=detected_stage,
            memory_context=memory_ctx,
            ocr_text=ocr_text or "",
        )
        step("Feedback returned", bool(feedback), f"{len(feedback)} chars")
        step("Feedback contains actionable content",
             "CTA" in feedback or "contrast" in feedback.lower(),
             feedback[:80].replace("\n", " ") + "…")
        step("Feedback ends with a follow-up question",
             feedback.strip().endswith("?"),
             "last char is '?'")

        # ── Step 6: Pattern candidate extracted ───────────────────────────────
        print(f"\n  {HEAD}Step 6 — Pattern candidate{RESET}")
        step("Pattern candidate returned", pattern_candidate is not None,
             str(pattern_candidate.get("name") if pattern_candidate else None))
        step("Candidate has required fields",
             all(k in pattern_candidate for k in ("name", "category", "description", "tags")),
             f"keys={list(pattern_candidate.keys())}")
        step("Candidate category valid", pattern_candidate["category"] in [
            "onboarding","kyc","trust-signals","cta-patterns","navigation","anti-patterns"
        ], pattern_candidate["category"])

        # ── Step 7: Store pending — nothing saved yet ─────────────────────────
        print(f"\n  {HEAD}Step 7 — Confirm nothing saved before approval{RESET}")
        conv.set_pending_pattern(user_id, pattern_candidate)
        yaml_files_before = list((tmp_path / "design-memory").rglob("*.yaml"))
        step("No YAML files before approval",
             len(yaml_files_before) == 0, f"{len(yaml_files_before)} files")
        step("Store is empty before approval", store.count() == 0, f"count={store.count()}")

        # ── Step 8: Approval via CLI simulation ───────────────────────────────
        print(f"\n  {HEAD}Step 8 — CLI approval simulation{RESET}")
        approval_phrases = ["save this", "Save This", "approve", "/approve", "keep this"]
        non_approval_phrases = ["no thanks", "what about the button?", "save", ""]
        for phrase in approval_phrases:
            step(f"is_approval_message('{phrase}')", is_approval_message(phrase))
        for phrase in non_approval_phrases:
            step(f"NOT approval: '{phrase}'", not is_approval_message(phrase))

        # Pop pending and save
        pending = conv.pop_pending_pattern(user_id)
        step("Pending pattern retrieved from session",
             pending is not None, str(pending.get("name") if pending else None))
        step("Session cleared after pop",
             conv.pop_pending_pattern(user_id) is None, "None")

        # ── Step 9: Save approved pattern ─────────────────────────────────────
        print(f"\n  {HEAD}Step 9 — Save approved pattern to design-memory/{RESET}")
        saved = await approve_and_save_pattern(
            store=store,
            pattern_data=pending,
            user_id=user_id,
            username="cli_validator",
        )
        step("Pattern saved to store", store.count() == 1, f"count={store.count()}")
        yaml_files_after = list((tmp_path / "design-memory").rglob("*.yaml"))
        step("YAML file created in design-memory/",
             len(yaml_files_after) == 1, yaml_files_after[0].name if yaml_files_after else "none")
        step("YAML in correct category folder",
             yaml_files_after[0].parent.name == saved.category,
             f"dir={yaml_files_after[0].parent.name}")

        # ── Step 10: Verify no raw screenshot path or PII in saved data ───────
        print(f"\n  {HEAD}Step 10 — No raw screenshot path or PII in saved data{RESET}")
        import yaml as _yaml
        saved_yaml = _yaml.safe_load(yaml_files_after[0].read_text())
        yaml_str = str(saved_yaml)

        step("No file path in YAML", "/tmp" not in yaml_str and "/Users" not in yaml_str,
             "no filesystem paths")
        step("No raw bytes in YAML", "\\xff" not in yaml_str and "0xFF" not in yaml_str,
             "no binary data")
        step("No email in YAML", "gmail.com" not in yaml_str and "@" not in yaml_str.replace("@cli_validator", ""),
             "no email addresses")
        step("approved_by is username not user_id",
             saved_yaml.get("approved_by") == "@cli_validator",
             f"approved_by={saved_yaml.get('approved_by')!r}")
        step("YAML contains only expected keys",
             set(saved_yaml.keys()) <= {
                 "pattern_id","name","category","tags","description",
                 "context","approved_by","approved_at","examples","anti_pattern_if"
             },
             f"keys={sorted(saved_yaml.keys())}")

        # ── Step 11: Memory retrieval now works ───────────────────────────────
        print(f"\n  {HEAD}Step 11 — Post-save memory retrieval{RESET}")
        memory_ctx_after = build_memory_context(store, saved.category)
        step("Memory context non-empty after save",
             len(memory_ctx_after) > 0, f"{len(memory_ctx_after)} chars")
        step("Saved pattern name in memory context",
             saved.name in memory_ctx_after, f"found '{saved.name}'")

        # ── Final YAML content display ─────────────────────────────────────────
        print(f"\n  {HEAD}Saved YAML:{RESET}")
        for line in yaml_files_after[0].read_text().splitlines():
            print(f"    {line}")

    _summary()


if __name__ == "__main__":
    asyncio.run(run())
