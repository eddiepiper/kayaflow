"""Tests for MemoryStore and Hermes memory retrieval."""

import json
import tempfile
from pathlib import Path

import pytest

from memory.pattern_schema import UXPattern
from memory.memory_store import MemoryStore
from memory.hermes_memory import retrieve_relevant_patterns, format_memory_context, build_memory_context


@pytest.fixture
def temp_store(tmp_path):
    store_path = tmp_path / "store.json"
    design_path = tmp_path / "design-memory"
    design_path.mkdir()
    return MemoryStore(store_path=store_path, design_memory_path=design_path)


@pytest.fixture
def sample_pattern():
    return UXPattern(
        name="Test Pattern",
        category="onboarding",
        description="A test UX pattern",
        context="Use in tests",
        anti_pattern_if="Overuse",
        tags=["test", "onboarding"],
    )


def test_save_and_retrieve_pattern(temp_store, sample_pattern):
    temp_store.save_pattern(sample_pattern)
    patterns = temp_store.get_patterns_by_category("onboarding")
    assert len(patterns) == 1
    assert patterns[0].name == "Test Pattern"


def test_yaml_file_created(temp_store, sample_pattern):
    temp_store.save_pattern(sample_pattern)
    yaml_files = list((temp_store.design_memory_path / "onboarding").glob("*.yaml"))
    assert len(yaml_files) == 1


def test_json_index_persisted(temp_store, sample_pattern):
    temp_store.save_pattern(sample_pattern)
    # Re-load store from same path
    store2 = MemoryStore(
        store_path=temp_store.store_path,
        design_memory_path=temp_store.design_memory_path,
    )
    assert store2.count() == 1


def test_count(temp_store, sample_pattern):
    assert temp_store.count() == 0
    temp_store.save_pattern(sample_pattern)
    assert temp_store.count() == 1


def test_get_patterns_empty_category(temp_store):
    patterns = temp_store.get_patterns_by_category("kyc")
    assert patterns == []


def test_retrieve_relevant_patterns_by_category(temp_store, sample_pattern):
    temp_store.save_pattern(sample_pattern)
    results = retrieve_relevant_patterns(temp_store, "onboarding")
    assert len(results) == 1
    assert results[0].name == "Test Pattern"


def test_retrieve_relevant_patterns_wrong_category(temp_store, sample_pattern):
    temp_store.save_pattern(sample_pattern)
    results = retrieve_relevant_patterns(temp_store, "kyc")
    assert len(results) == 0


def test_format_memory_context_empty():
    result = format_memory_context([])
    assert result == ""


def test_format_memory_context_with_pattern(sample_pattern):
    result = format_memory_context([sample_pattern])
    assert "Test Pattern" in result
    assert "onboarding" in result


def test_build_memory_context_empty_store(temp_store):
    result = build_memory_context(temp_store, "onboarding")
    assert result == ""


def test_build_memory_context_with_patterns(temp_store, sample_pattern):
    temp_store.save_pattern(sample_pattern)
    result = build_memory_context(temp_store, "onboarding")
    assert "Test Pattern" in result
