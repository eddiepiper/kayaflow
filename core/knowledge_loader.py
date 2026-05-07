"""
Knowledge loader for KayaFlow Senior CX Knowledge Pack.
Selects relevant docs from docs/ and patterns-library/ based on context keywords.
No vector DB — keyword-based selection only.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).parent.parent / "docs"
PATTERNS_DIR = Path(__file__).parent.parent / "patterns-library"

# Always loaded regardless of context
CORE_DOCS = [
    "design.md",
    "cx-review-rubric.md",
    "tone-guide.md",
]

# Keyword → doc file mappings
KEYWORD_DOC_MAP: list[tuple[set[str], list[str]]] = [
    (
        {"wealth", "structured deposit", "structured product", "interest", "return",
         "returns", "principal", "maturity", "guaranteed", "up to", "p.a.", "yield",
         "investment", "invest", "deposit", "capital", "bond", "fund"},
        ["banking-trust-patterns.md", "wealth-product-ux.md",
         "disclosure-placement.md", "cta-timing.md"],
    ),
    (
        {"onboarding", "kyc", "nric", "income", "employment", "identity",
         "sign up", "signup", "register", "verification", "singpass"},
        ["onboarding-psychology.md", "banking-trust-patterns.md", "cognitive-load.md"],
    ),
    (
        {"cta", "button", "proceed", "submit", "confirm", "checkout", "commit",
         "subscribe", "agree", "continue"},
        ["cta-timing.md", "cognitive-load.md"],
    ),
    (
        {"disclosure", "risk", "disclaimer", "terms", "conditions", "footnote",
         "fine print", "notice", "important"},
        ["disclosure-placement.md", "banking-trust-patterns.md"],
    ),
    (
        {"cognitive", "load", "complex", "confusing", "overwhelming", "unclear",
         "navigation", "menu", "tabs", "flow"},
        ["cognitive-load.md"],
    ),
]

# Keyword → pattern file mappings
KEYWORD_PATTERN_MAP: list[tuple[set[str], list[str]]] = [
    (
        {"return", "returns", "interest", "principal", "guaranteed", "up to",
         "yield", "p.a.", "rate", "3.37"},
        ["trust-signals/contextual-disclosure-anchor.md",
         "disclosure-patterns/inline-risk-disclosure.md",
         "anti-patterns/buried-risk-disclosure.md"],
    ),
    (
        {"cta", "proceed", "invest", "subscribe", "confirm", "button"},
        ["cta-patterns/cta-after-comprehension.md",
         "comprehension-gates/risk-acknowledgement-before-cta.md"],
    ),
    (
        {"onboarding", "kyc", "nric", "income", "data collection"},
        ["onboarding-friction/premature-data-collection.md",
         "trust-signals/trust-before-data-collection.md"],
    ),
    (
        {"disclosure", "risk", "buried", "footer", "fine print"},
        ["anti-patterns/buried-risk-disclosure.md",
         "disclosure-patterns/inline-risk-disclosure.md"],
    ),
]

MAX_KNOWLEDGE_CHARS = 10000


def _read_doc(filename: str) -> str:
    path = DOCS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning(f"Knowledge doc not found: {filename}")
    return ""


def _read_pattern(relative_path: str) -> str:
    path = PATTERNS_DIR / relative_path
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning(f"Pattern file not found: {relative_path}")
    return ""


def _matches(context_lower: str, keywords: set[str]) -> bool:
    return any(kw in context_lower for kw in keywords)


def load_knowledge(context: str) -> str:
    """
    Select and return relevant knowledge docs as a single context string.
    context: combined text from OCR output, journey stage, and any user-provided context.
    """
    context_lower = context.lower()

    # Core docs always loaded
    selected_docs: list[str] = list(CORE_DOCS)
    selected_patterns: list[str] = []

    # Keyword-selected docs
    for keywords, docs in KEYWORD_DOC_MAP:
        if _matches(context_lower, keywords):
            for doc in docs:
                if doc not in selected_docs:
                    selected_docs.append(doc)

    # Keyword-selected patterns
    for keywords, patterns in KEYWORD_PATTERN_MAP:
        if _matches(context_lower, keywords):
            for p in patterns:
                if p not in selected_patterns:
                    selected_patterns.append(p)

    logger.debug(f"Knowledge loader selected docs={selected_docs}, patterns={selected_patterns}")

    # Build context block
    sections: list[str] = []
    total_chars = 0

    for filename in selected_docs:
        content = _read_doc(filename)
        if content and total_chars + len(content) <= MAX_KNOWLEDGE_CHARS:
            sections.append(content.strip())
            total_chars += len(content)

    for rel_path in selected_patterns:
        content = _read_pattern(rel_path)
        if content and total_chars + len(content) <= MAX_KNOWLEDGE_CHARS:
            sections.append(content.strip())
            total_chars += len(content)

    if not sections:
        return ""

    return "\n\n---\n\n".join(sections)
