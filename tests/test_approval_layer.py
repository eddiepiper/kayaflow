"""Tests for the approval layer — pattern approval detection and saving."""

import pytest

from core.approval_layer import is_approval_message


@pytest.mark.parametrize("text,expected", [
    ("save this", True),
    ("Save This", True),
    ("approve", True),
    ("APPROVE", True),
    ("yes save", True),
    ("keep this", True),
    ("looks good save", True),
    ("/approve", True),
    ("/approve now", True),
    ("no thanks", False),
    ("what about the button?", False),
    ("send me another screen", False),
    ("", False),
    ("save", False),  # Partial match not enough
])
def test_is_approval_message(text, expected):
    assert is_approval_message(text) == expected


@pytest.mark.asyncio
async def test_approve_and_save_pattern(tmp_path):
    from memory.memory_store import MemoryStore
    from core.approval_layer import approve_and_save_pattern

    store = MemoryStore(
        store_path=tmp_path / "store.json",
        design_memory_path=tmp_path / "design-memory",
    )

    pattern_data = {
        "name": "Test Approval Pattern",
        "category": "onboarding",
        "description": "Pattern saved via approval flow",
        "context": "Test context",
        "anti_pattern_if": "Test anti",
        "tags": ["approval", "test"],
    }

    saved = await approve_and_save_pattern(
        store=store,
        pattern_data=pattern_data,
        user_id=12345,
        username="testuser",
    )

    assert saved.name == "Test Approval Pattern"
    assert saved.approved_by == "@testuser"
    assert store.count() == 1


@pytest.mark.asyncio
async def test_approve_and_save_without_username(tmp_path):
    from memory.memory_store import MemoryStore
    from core.approval_layer import approve_and_save_pattern

    store = MemoryStore(
        store_path=tmp_path / "store.json",
        design_memory_path=tmp_path / "design-memory",
    )

    saved = await approve_and_save_pattern(
        store=store,
        pattern_data={"name": "Anon Pattern", "category": "kyc"},
        user_id=99999,
        username="",
    )

    assert "user:99999" in saved.approved_by
