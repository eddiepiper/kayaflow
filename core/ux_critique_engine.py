from __future__ import annotations

import base64
import json
import logging

import anthropic

from config.settings import CLAUDE_CRITIQUE_MODEL, CLAUDE_QUICK_MODEL, JOURNEY_CATEGORY_LABELS
from config.prompts import (
    SYSTEM_PROMPT,
    CASUAL_CHAT_SYSTEM_PROMPT,
    JOURNEY_CONTEXT_PROMPT,
    CRITIQUE_WITH_MEMORY_PROMPT,
    PATTERN_EXTRACTION_PROMPT,
    FOLLOW_UP_PROMPT,
)
from core.knowledge_loader import load_knowledge

logger = logging.getLogger(__name__)

KNOWLEDGE_PACK_INSTRUCTION = """
You have been provided with a Senior CX Knowledge Pack above.
Use it silently to inform your critique. Focus on: trust, comprehension, CTA timing, disclosure placement, cognitive load, and customer progression readiness.
Avoid generic UX comments. Produce senior-level critique grounded in the principles provided.
Do not quote or reproduce the knowledge pack in your response.
"""


async def critique_screenshot(
    client: anthropic.AsyncAnthropic,
    image_bytes: bytes,
    journey_stage: str = "unknown",
    memory_context: str = "",
    ocr_text: str = "",
    conversation_history: list[dict] | None = None,
) -> tuple[str, dict | None]:
    """
    Analyze a UI screenshot and return (feedback_text, extracted_pattern | None).
    """
    # Build knowledge context from OCR text + journey stage
    knowledge_context_input = f"{journey_stage} {ocr_text}".strip()
    knowledge = load_knowledge(knowledge_context_input)

    # Build system prompt
    system = SYSTEM_PROMPT
    if knowledge:
        system += f"\n\n# Senior CX Knowledge Pack\n\n{knowledge}\n\n{KNOWLEDGE_PACK_INSTRUCTION}"
    if journey_stage != "unknown":
        stage_label = JOURNEY_CATEGORY_LABELS.get(journey_stage, journey_stage)
        system += JOURNEY_CONTEXT_PROMPT.format(
            stage=journey_stage, stage_label=stage_label
        )
    if memory_context:
        system += CRITIQUE_WITH_MEMORY_PROMPT.format(memory_context=memory_context)

    # Build user message content
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    user_content: list[dict] = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_b64,
            },
        }
    ]

    if ocr_text:
        user_content.append({
            "type": "text",
            "text": f"Text extracted from the screen:\n{ocr_text}\n\nPlease review the UX of this screen.",
        })
    else:
        user_content.append({"type": "text", "text": "Please review the UX of this screen."})

    messages = (conversation_history or []) + [{"role": "user", "content": user_content}]

    response = await client.messages.create(
        model=CLAUDE_CRITIQUE_MODEL,
        max_tokens=800,
        system=system,
        messages=messages,
    )

    feedback = response.content[0].text.strip()

    # Attempt pattern extraction as a second, lightweight call
    pattern = await _extract_pattern(client, feedback, journey_stage)

    return feedback, pattern


async def handle_follow_up(
    client: anthropic.AsyncAnthropic,
    user_message: str,
    conversation_history: list[dict],
    journey_stage: str = "unknown",
) -> str:
    """Handle a follow-up text message in an ongoing review session."""
    system = SYSTEM_PROMPT
    if journey_stage != "unknown":
        stage_label = JOURNEY_CATEGORY_LABELS.get(journey_stage, journey_stage)
        system += JOURNEY_CONTEXT_PROMPT.format(
            stage=journey_stage, stage_label=stage_label
        )

    messages = conversation_history + [{"role": "user", "content": user_message}]

    response = await client.messages.create(
        model=CLAUDE_CRITIQUE_MODEL,
        max_tokens=500,
        system=system,
        messages=messages,
    )

    return response.content[0].text.strip()


async def handle_casual_chat(
    client: anthropic.AsyncAnthropic,
    user_message: str,
) -> str:
    """Handle casual chat messages with Singapore PM teammate tone."""
    response = await client.messages.create(
        model=CLAUDE_QUICK_MODEL,
        max_tokens=150,
        system=CASUAL_CHAT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text.strip()


async def _extract_pattern(
    client: anthropic.AsyncAnthropic,
    feedback: str,
    category: str,
) -> dict | None:
    """Extract a reusable pattern from feedback. Returns None if no pattern found."""
    try:
        prompt = PATTERN_EXTRACTION_PROMPT.format(category=category)
        response = await client.messages.create(
            model=CLAUDE_CRITIQUE_MODEL,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": f"Feedback given:\n{feedback}\n\n{prompt}",
                }
            ],
        )
        raw = response.content[0].text.strip()
        # Find JSON in response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return None
        data = json.loads(raw[start:end])
        if data.get("found_pattern") and data.get("pattern"):
            return data["pattern"]
        return None
    except (json.JSONDecodeError, KeyError, Exception) as e:
        logger.debug(f"Pattern extraction skipped: {e}")
        return None
