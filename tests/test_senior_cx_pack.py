"""Tests for senior CX pack integration with critique engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_client():
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text=(
        "The CTA appears before the user has understood the conditions attached "
        "to principal protection. Users may proceed with more confidence than "
        "the disclosures support. Clarify whether 3.37% is guaranteed, "
        "conditional, or maximum potential return.\n\n"
        "What is the intended journey stage for this screen?"
    ))]
    client.messages.create = AsyncMock(return_value=response)
    return client


@pytest.fixture
def sample_image_bytes():
    from PIL import Image
    import io
    img = Image.new("RGB", (100, 100), color=(240, 240, 245))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


# ── knowledge loader integration ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_critique_includes_knowledge_in_system_prompt(mock_client, sample_image_bytes):
    """Verify critique engine passes knowledge context into system prompt."""
    with patch("core.ux_critique_engine._extract_pattern", new_callable=AsyncMock, return_value=None):
        from core.ux_critique_engine import critique_screenshot
        await critique_screenshot(
            client=mock_client,
            image_bytes=sample_image_bytes,
            journey_stage="unknown",
            ocr_text="earn 3.37% returns principal protected",
        )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system_prompt = call_kwargs.get("system", "")
    assert "Senior CX Knowledge Pack" in system_prompt


@pytest.mark.asyncio
async def test_wealth_ocr_text_triggers_banking_docs(mock_client, sample_image_bytes):
    """Wealth-related OCR text causes banking trust docs to be included."""
    with patch("core.ux_critique_engine._extract_pattern", new_callable=AsyncMock, return_value=None):
        from core.ux_critique_engine import critique_screenshot
        await critique_screenshot(
            client=mock_client,
            image_bytes=sample_image_bytes,
            journey_stage="unknown",
            ocr_text="structured deposit 3.37% p.a. principal protected",
        )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system = call_kwargs.get("system", "")
    assert "Banking Trust Patterns" in system
    assert "Wealth Product UX" in system


@pytest.mark.asyncio
async def test_onboarding_stage_triggers_onboarding_docs(mock_client, sample_image_bytes):
    """Onboarding journey stage loads onboarding psychology doc."""
    with patch("core.ux_critique_engine._extract_pattern", new_callable=AsyncMock, return_value=None):
        from core.ux_critique_engine import critique_screenshot
        await critique_screenshot(
            client=mock_client,
            image_bytes=sample_image_bytes,
            journey_stage="onboarding",
            ocr_text="enter your nric to continue",
        )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system = call_kwargs.get("system", "")
    assert "Onboarding Psychology" in system


@pytest.mark.asyncio
async def test_knowledge_pack_instruction_present(mock_client, sample_image_bytes):
    """Senior CX instruction block is always added when knowledge is loaded."""
    with patch("core.ux_critique_engine._extract_pattern", new_callable=AsyncMock, return_value=None):
        from core.ux_critique_engine import critique_screenshot
        await critique_screenshot(
            client=mock_client,
            image_bytes=sample_image_bytes,
        )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system = call_kwargs.get("system", "")
    assert "senior-level critique" in system.lower() or "Senior CX Knowledge Pack" in system


@pytest.mark.asyncio
async def test_raw_knowledge_not_reproduced_in_response(mock_client, sample_image_bytes):
    """Knowledge pack instruction tells model not to reproduce raw content."""
    with patch("core.ux_critique_engine._extract_pattern", new_callable=AsyncMock, return_value=None):
        from core.ux_critique_engine import critique_screenshot
        await critique_screenshot(
            client=mock_client,
            image_bytes=sample_image_bytes,
            ocr_text="invest now structured deposit returns",
        )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system = call_kwargs.get("system", "")
    # Instruction to suppress raw pack in response must be present
    assert "Do not quote or reproduce the knowledge pack" in system


@pytest.mark.asyncio
async def test_critique_runs_without_internet(mock_client, sample_image_bytes):
    """Full critique call completes using only local files — no network needed."""
    with patch("core.ux_critique_engine._extract_pattern", new_callable=AsyncMock, return_value=None):
        from core.ux_critique_engine import critique_screenshot
        feedback, pattern = await critique_screenshot(
            client=mock_client,
            image_bytes=sample_image_bytes,
            journey_stage="onboarding",
            ocr_text="nric income employment details",
        )
    assert isinstance(feedback, str)
    assert len(feedback) > 0


@pytest.mark.asyncio
async def test_no_knowledge_loaded_for_generic_context(mock_client, sample_image_bytes):
    """Generic context still loads core docs (design.md, rubric, tone-guide)."""
    with patch("core.ux_critique_engine._extract_pattern", new_callable=AsyncMock, return_value=None):
        from core.ux_critique_engine import critique_screenshot
        await critique_screenshot(
            client=mock_client,
            image_bytes=sample_image_bytes,
            ocr_text="hello world",
        )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system = call_kwargs.get("system", "")
    # Core docs always present
    assert "KayaFlow Senior CX Design Principles" in system
    assert "KayaFlow CX Review Rubric" in system
