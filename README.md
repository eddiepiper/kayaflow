# KayaFlow

[![Tests](https://img.shields.io/badge/tests-32%20passed-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](requirements.txt)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![Version](https://img.shields.io/badge/version-v1.0--foundation-orange)](https://github.com/eddiepiper/kayaflow/releases/tag/v1.0-foundation)

**Your AI UX Kaki for Customer Journeys**

KayaFlow is a Telegram-first AI UX review bot powered by Hermes-style memory. Upload UI screenshots or customer journey screens — KayaFlow reviews the UX, gives clear Singapore-style conversational feedback, asks follow-up questions, and saves approved reusable UX patterns into a GitHub-ready design memory structure.

---

## Features

- **Telegram-native**: Send screenshots directly in Telegram — no dashboards, no friction
- **UX Critique Engine**: Powered by Claude, delivers actionable SG-style feedback (clear lah, not textbook)
- **Journey Context**: Understands where a screen sits in the user journey (onboarding, KYC, checkout, etc.)
- **Follow-up Conversations**: Asks clarifying questions to give better feedback
- **Design Memory**: Approved patterns saved as structured YAML/JSON in `design-memory/`
- **OCR Support**: Extracts text from UI screenshots for deeper analysis
- **Anti-pattern Detection**: Flags dark patterns, confusing flows, trust-breaking elements

---

## Quick Start

```bash
# 1. Clone and setup
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify setup
bash scripts/verify.sh

# 4. Run the bot
bash scripts/run_bot.sh
```

---

## Architecture

```
KayaFlow/
├── bot/                    # Telegram bot layer
│   ├── telegram_bot.py     # Bot initialization and webhook/polling setup
│   └── handlers.py         # Message, photo, and command handlers
├── core/                   # Business logic
│   ├── ux_critique_engine.py   # Claude-powered UX analysis
│   ├── image_intake.py         # Image download and preprocessing
│   ├── ocr_extractor.py        # Text extraction from screenshots
│   ├── journey_context.py      # User journey stage detection
│   ├── conversation_manager.py # Multi-turn conversation state
│   └── approval_layer.py       # Pattern approval and saving flow
├── memory/                 # Hermes memory system
│   ├── hermes_memory.py    # Memory retrieval and augmentation
│   ├── memory_store.py     # JSON-based pattern storage
│   └── pattern_schema.py   # Pattern data models
├── config/
│   ├── settings.py         # Environment config
│   └── prompts.py          # System and critique prompts
└── design-memory/          # GitHub-ready pattern library
    ├── onboarding/
    ├── kyc/
    ├── trust-signals/
    ├── cta-patterns/
    ├── navigation/
    ├── anti-patterns/
    └── journey-reviews/
```

---

## Environment Variables

See `.env.example` for all required configuration.

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `ANTHROPIC_API_KEY` | Claude API key |
| `MEMORY_STORE_PATH` | Path to memory store JSON |
| `DESIGN_MEMORY_PATH` | Path to design-memory directory |
| `OCR_ENABLED` | Enable/disable OCR (true/false) |

---

## Senior CX Knowledge Pack

KayaFlow V1.1 includes a local reviewer knowledge pack covering:

- enterprise CX review principles
- banking trust patterns
- wealth product UX
- disclosure placement
- CTA timing
- onboarding psychology
- cognitive load
- Singapore PM tone guide

This upgrades KayaFlow from a generic UX reviewer into a structured senior CX reviewer. The knowledge pack is loaded locally — no vector DB, no internet required at runtime. Relevant docs are selected automatically from context keywords (e.g. "structured deposit", "NRIC", "returns", "CTA").

---

## Design Memory Structure

Approved patterns are saved as YAML files in `design-memory/`:

```yaml
# design-memory/onboarding/progressive-disclosure-v1.yaml
pattern_id: "onboarding-001"
name: "Progressive Disclosure Onboarding"
category: "onboarding"
tags: ["onboarding", "progressive", "low-friction"]
description: "Show only essential fields first, reveal more on demand"
context: "Works well when user trust is low or form is long"
approved_by: "@user"
approved_at: "2026-05-07"
examples: []
anti_pattern_if: "All fields shown at once with no grouping"
```

---

## Contributing

Patterns saved via KayaFlow are committed to `design-memory/` — making this a living design system anyone on the team can reference.

---

*Built with Claude + python-telegram-bot + Singapore can-do energy* 🇸🇬
