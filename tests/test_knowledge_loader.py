"""Tests for knowledge_loader — selection logic, no internet access required."""

import pytest
from core.knowledge_loader import load_knowledge, DOCS_DIR, PATTERNS_DIR


# ── core docs always loaded ───────────────────────────────────────────────────

def test_always_loads_design_md():
    result = load_knowledge("random context")
    assert "KayaFlow Senior CX Design Principles" in result


def test_always_loads_cx_review_rubric():
    result = load_knowledge("random context")
    assert "KayaFlow CX Review Rubric" in result


def test_always_loads_tone_guide():
    result = load_knowledge("random context")
    assert "KayaFlow Tone Guide" in result


# ── wealth / structured deposit context ──────────────────────────────────────

def test_wealth_context_loads_wealth_product_ux():
    result = load_knowledge("structured deposit with 3.37% returns")
    assert "Wealth Product UX" in result


def test_wealth_context_loads_banking_trust_patterns():
    result = load_knowledge("wealth product with guaranteed principal")
    assert "Banking Trust Patterns" in result


def test_wealth_context_loads_disclosure_placement():
    result = load_knowledge("investment return p.a. maturity")
    assert "Disclosure Placement" in result


def test_wealth_context_loads_cta_timing():
    result = load_knowledge("structured deposit invest now")
    assert "CTA Timing" in result


def test_structured_deposit_keyword():
    result = load_knowledge("structured deposit onboarding")
    assert "Wealth Product UX" in result


def test_interest_keyword():
    result = load_knowledge("earn 3.37% interest on your deposit")
    assert "Banking Trust Patterns" in result


# ── onboarding / KYC context ─────────────────────────────────────────────────

def test_onboarding_context_loads_onboarding_psychology():
    result = load_knowledge("onboarding flow step 1")
    assert "Onboarding Psychology" in result


def test_kyc_context_loads_onboarding_psychology():
    result = load_knowledge("kyc identity verification")
    assert "Onboarding Psychology" in result


def test_nric_keyword_loads_cognitive_load():
    result = load_knowledge("please enter your nric number")
    assert "Cognitive Load" in result


def test_onboarding_context_loads_banking_trust():
    result = load_knowledge("onboarding for wealth product")
    assert "Banking Trust Patterns" in result


# ── pattern library selection ─────────────────────────────────────────────────

def test_return_keyword_loads_contextual_disclosure_pattern():
    result = load_knowledge("earn 3.37% returns")
    assert "Contextual Disclosure Anchor" in result


def test_cta_keyword_loads_cta_after_comprehension():
    result = load_knowledge("invest now cta button")
    assert "CTA After Comprehension" in result


def test_disclosure_keyword_loads_buried_risk_pattern():
    result = load_knowledge("risk disclosure footer")
    assert "Buried Risk Disclosure" in result


def test_onboarding_loads_premature_data_collection():
    result = load_knowledge("onboarding nric data collection")
    assert "Premature Data Collection" in result


# ── no raw repo content in output ─────────────────────────────────────────────

def test_no_raw_github_urls_in_output():
    result = load_knowledge("onboarding wealth structured deposit")
    assert "github.com" not in result.lower()


def test_no_node_modules_content():
    result = load_knowledge("anything")
    assert "node_modules" not in result
    assert "package.json" not in result


# ── empty context still returns core docs ────────────────────────────────────

def test_empty_context_returns_core_docs():
    result = load_knowledge("")
    assert "KayaFlow Senior CX Design Principles" in result
    assert len(result) > 100


# ── char budget respected ────────────────────────────────────────────────────

def test_output_within_char_budget():
    from core.knowledge_loader import MAX_KNOWLEDGE_CHARS
    result = load_knowledge("wealth structured deposit onboarding kyc nric cta invest returns principal")
    assert len(result) <= MAX_KNOWLEDGE_CHARS + 500  # small tolerance for separators


# ── docs files exist ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", [
    "design.md", "cx-review-rubric.md", "tone-guide.md",
    "banking-trust-patterns.md", "wealth-product-ux.md",
    "disclosure-placement.md", "cta-timing.md",
    "onboarding-psychology.md", "cognitive-load.md",
])
def test_doc_file_exists(filename):
    assert (DOCS_DIR / filename).exists(), f"Missing: docs/{filename}"


@pytest.mark.parametrize("rel_path", [
    "trust-signals/contextual-disclosure-anchor.md",
    "trust-signals/trust-before-data-collection.md",
    "disclosure-patterns/inline-risk-disclosure.md",
    "comprehension-gates/risk-acknowledgement-before-cta.md",
    "cta-patterns/cta-after-comprehension.md",
    "onboarding-friction/premature-data-collection.md",
    "anti-patterns/buried-risk-disclosure.md",
])
def test_pattern_file_exists(rel_path):
    assert (PATTERNS_DIR / rel_path).exists(), f"Missing: patterns-library/{rel_path}"
