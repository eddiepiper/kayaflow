"""Tests for UX critique engine — mocks Claude API calls."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_claude_client():
    client = AsyncMock()
    response = MagicMock()
    response.content = [MagicMock(text="Great screen! Works well: clear CTA. Issues: contrast low. Try this: increase button contrast.")]
    client.messages.create = AsyncMock(return_value=response)
    return client


@pytest.fixture
def sample_image_bytes():
    # Minimal valid JPEG bytes (1x1 white pixel)
    return bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
        0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
        0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0x8C,
        0xFF, 0xD9,
    ])


@pytest.mark.asyncio
async def test_critique_screenshot_returns_feedback(mock_claude_client, sample_image_bytes):
    with patch("core.ux_critique_engine._extract_pattern", new_callable=AsyncMock, return_value=None):
        from core.ux_critique_engine import critique_screenshot
        feedback, pattern = await critique_screenshot(
            client=mock_claude_client,
            image_bytes=sample_image_bytes,
        )
    assert isinstance(feedback, str)
    assert len(feedback) > 0
    assert pattern is None


@pytest.mark.asyncio
async def test_critique_screenshot_with_journey_stage(mock_claude_client, sample_image_bytes):
    with patch("core.ux_critique_engine._extract_pattern", new_callable=AsyncMock, return_value=None):
        from core.ux_critique_engine import critique_screenshot
        feedback, _ = await critique_screenshot(
            client=mock_claude_client,
            image_bytes=sample_image_bytes,
            journey_stage="onboarding",
        )
    assert feedback
    # Verify system prompt included journey context
    call_kwargs = mock_claude_client.messages.create.call_args.kwargs
    assert "onboarding" in call_kwargs.get("system", "").lower()


@pytest.mark.asyncio
async def test_extract_pattern_invalid_json_returns_none(mock_claude_client):
    mock_claude_client.messages.create.return_value.content[0].text = "not json at all"
    from core.ux_critique_engine import _extract_pattern
    result = await _extract_pattern(mock_claude_client, "some feedback", "onboarding")
    assert result is None


@pytest.mark.asyncio
async def test_extract_pattern_no_pattern_found(mock_claude_client):
    mock_claude_client.messages.create.return_value.content[0].text = '{"found_pattern": false}'
    from core.ux_critique_engine import _extract_pattern
    result = await _extract_pattern(mock_claude_client, "some feedback", "onboarding")
    assert result is None


@pytest.mark.asyncio
async def test_extract_pattern_valid(mock_claude_client):
    mock_claude_client.messages.create.return_value.content[0].text = '''{
        "found_pattern": true,
        "pattern": {
            "name": "Test Pattern",
            "category": "onboarding",
            "description": "A test pattern",
            "context": "Use in tests",
            "anti_pattern_if": "Never",
            "tags": ["test"]
        }
    }'''
    from core.ux_critique_engine import _extract_pattern
    result = await _extract_pattern(mock_claude_client, "some feedback", "onboarding")
    assert result is not None
    assert result["name"] == "Test Pattern"
