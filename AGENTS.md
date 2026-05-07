# KayaFlow — Codex Instructions

## Project Overview

KayaFlow is a Telegram-first AI UX review bot. Users send UI screenshots via Telegram; the bot analyzes UX, gives Singapore-style conversational feedback, and saves approved patterns to a structured design memory library.

## Tech Stack

- **Runtime**: Python 3.11+
- **Bot Framework**: python-telegram-bot v21+
- **AI**: Anthropic Codex API (Codex-sonnet-4-6 default, Codex-haiku-4-5-20251001 for quick responses)
- **OCR**: pytesseract + Pillow
- **Memory**: JSON file store (upgradeable to SQLite)
- **Config**: python-dotenv

## Key Design Decisions

- **Hermes-style memory**: Structured pattern retrieval — before critiquing a screen, load relevant past patterns from `design-memory/` to provide context-aware feedback
- **Singapore tone**: Feedback should be direct, practical, friendly — not academic. Use "lah", "leh", "can try" where appropriate but not forced
- **Approval-gated memory**: Patterns are NOT auto-saved — user must explicitly approve via `/approve` or reply "save this" before patterns write to disk
- **Stateless per-session**: Conversation state is in-memory per session; design memory persists to disk

## File Responsibilities

| File | Purpose |
|---|---|
| `bot/telegram_bot.py` | Bot init, polling/webhook, error handling |
| `bot/handlers.py` | Route messages to core logic |
| `core/ux_critique_engine.py` | Main Codex call for UX analysis |
| `core/image_intake.py` | Download + preprocess Telegram photos |
| `core/ocr_extractor.py` | Extract text from screenshots |
| `core/journey_context.py` | Detect journey stage from image/text |
| `core/conversation_manager.py` | Per-user conversation state |
| `core/approval_layer.py` | Handle pattern approval flow |
| `memory/hermes_memory.py` | Load relevant memories for context |
| `memory/memory_store.py` | Read/write pattern YAML files |
| `memory/pattern_schema.py` | Pydantic models for patterns |

## Development Commands

```bash
# Run bot locally
bash scripts/run_bot.sh

# Verify environment
bash scripts/verify.sh

# Seed with example patterns
python scripts/seed_memory.py

# Run tests
pytest tests/ -v
```

## Adding New Journey Categories

1. Create folder in `design-memory/<new-category>/`
2. Add category to `JOURNEY_CATEGORIES` in `config/settings.py`
3. Add prompts for category in `config/prompts.py`
4. Update `core/journey_context.py` detection logic

## Memory Pattern Format

See `memory/pattern_schema.py` for the Pydantic model. Patterns are stored as YAML in `design-memory/<category>/`. Filenames follow: `<category>-<slug>-v<n>.yaml`

## Tone Guidelines

- Direct and practical, not textbook
- SG-friendly but professional
- Short sentences, clear action items
- End critique with 1-2 specific "try this" suggestions
- Never say "it depends" without giving a concrete example
