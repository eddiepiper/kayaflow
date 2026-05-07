"""Tests for casual chat tone routing and format rules."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.handlers import is_casual_chat
from config.prompts import CASUAL_CHAT_SYSTEM_PROMPT, SYSTEM_PROMPT


# ── detection ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    # exact matches
    "hi", "hello", "hey", "yo",
    "how are you", "how r u",
    "what can you do", "what do you do", "who are you",
    "tell me about yourself", "what is kayaflow",
    "are you useful",
    "thanks", "thank you", "thx", "noted", "got it",
    "ok", "okay", "cool", "alright", "sure",
    "ok thanks", "thanks lah", "ok lah",
    # punctuation variants — all must work
    "hi!", "hello!", "hey!", "thanks!",
    "how are you?", "what can you do?", "who are you?",
    "hi.", "thanks.",
    # partial / extended phrasing (substring matches)
    "how are you ah",        # SG suffix
    "how are you leh",
    "what scope can you do", # typo variant
    "what can u do",
    "who are you exactly",
    "tell me about kayaflow",
])
def test_is_casual_chat_true(text):
    assert is_casual_chat(text) is True, f"Expected True for: {text!r}"


@pytest.mark.parametrize("text", [
    "the CTA button looks wrong",
    "why is the disclosure below the fold",
    "save this",
    "/approve",
    "what do you think about this onboarding screen",
    "is the trust signal strong enough",
    "the font size seems off",
    "can you check the KYC flow",
    "review this screen",
    "is the disclosure placement correct",
])
def test_is_casual_chat_false(text):
    assert is_casual_chat(text) is False, f"Expected False for: {text!r}"


def test_is_casual_chat_case_insensitive():
    assert is_casual_chat("How Are You") is True
    assert is_casual_chat("HELLO") is True
    assert is_casual_chat("THANKS") is True
    assert is_casual_chat("WHAT CAN YOU DO") is True


def test_is_casual_chat_strips_all_punctuation():
    assert is_casual_chat("hello!") is True
    assert is_casual_chat("hi!!") is True
    assert is_casual_chat("thanks,") is True
    assert is_casual_chat("how are you?!") is True


def test_is_casual_chat_trailing_period():
    assert is_casual_chat("hello.") is True
    assert is_casual_chat("thanks.") is True


# ── prompt format rules ───────────────────────────────────────────────────────

def test_casual_prompt_under_80_word_rule():
    assert "80 words" in CASUAL_CHAT_SYSTEM_PROMPT


def test_casual_prompt_no_markdown_headings_rule():
    assert "markdown headings" in CASUAL_CHAT_SYSTEM_PROMPT.lower()


def test_casual_prompt_no_bullet_dash_rule():
    assert "bullet" in CASUAL_CHAT_SYSTEM_PROMPT.lower()


def test_casual_prompt_no_em_dash_rule():
    assert "em dash" in CASUAL_CHAT_SYSTEM_PROMPT.lower()


def test_casual_prompt_singapore_tone():
    assert "lah" in CASUAL_CHAT_SYSTEM_PROMPT


def test_casual_prompt_no_haha_or_great_question():
    assert "Haha" not in CASUAL_CHAT_SYSTEM_PROMPT or "Do not start with" in CASUAL_CHAT_SYSTEM_PROMPT
    assert "Great question" not in CASUAL_CHAT_SYSTEM_PROMPT or "Do not start with" in CASUAL_CHAT_SYSTEM_PROMPT


# ── casual prompt is separate from critique prompt ────────────────────────────

def test_casual_and_critique_prompts_are_different():
    assert CASUAL_CHAT_SYSTEM_PROMPT != SYSTEM_PROMPT


def test_critique_prompt_unchanged():
    """Critique system prompt still contains senior CX reviewer framing."""
    assert "senior CX and product reviewer" in SYSTEM_PROMPT
    assert "disclosure" in SYSTEM_PROMPT.lower()
    assert "follow-up question" in SYSTEM_PROMPT.lower()


# ── casual chat engine call ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_handle_casual_chat_uses_casual_prompt():
    """handle_casual_chat passes CASUAL_CHAT_SYSTEM_PROMPT, not SYSTEM_PROMPT."""
    from core.ux_critique_engine import handle_casual_chat

    mock_client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text="Doing okay lah. Send the next screen when ready.")]
    mock_client.messages.create = AsyncMock(return_value=response)

    result = await handle_casual_chat(mock_client, "how are you")

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["system"] == CASUAL_CHAT_SYSTEM_PROMPT
    assert call_kwargs["system"] != SYSTEM_PROMPT
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_handle_casual_chat_max_tokens_low():
    """Casual chat uses a lower token budget than critique (150 vs 800)."""
    from core.ux_critique_engine import handle_casual_chat

    mock_client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text="Send the next screen when ready.")]
    mock_client.messages.create = AsyncMock(return_value=response)

    await handle_casual_chat(mock_client, "thanks")

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["max_tokens"] <= 200


# ── critique mode format unchanged ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_critique_does_not_use_casual_prompt():
    """Screenshot critique still uses SYSTEM_PROMPT not casual prompt."""
    from core.ux_critique_engine import critique_screenshot
    import io
    from PIL import Image

    img = Image.new("RGB", (50, 50), color=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    mock_client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text="The CTA appears before comprehension is established. Is this a checkout screen?")]
    mock_client.messages.create = AsyncMock(return_value=response)

    from unittest.mock import patch
    with patch("core.ux_critique_engine._extract_pattern", new_callable=AsyncMock, return_value=None):
        feedback, _ = await critique_screenshot(
            client=mock_client,
            image_bytes=image_bytes,
        )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system = call_kwargs.get("system", "")
    assert "senior CX and product reviewer" in system
    assert CASUAL_CHAT_SYSTEM_PROMPT not in system
