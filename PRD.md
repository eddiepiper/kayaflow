# KayaFlow — Product Requirements Document

**Version**: 1.0
**Status**: Active Development
**Owner**: eddiepiper@gmail.com
**Created**: 2026-05-07

---

## Problem Statement

UX reviews happen too late, take too long, and produce feedback that's hard to act on. Designers either wait for formal critique sessions or get generic comments that don't account for their specific user journey context. There's no persistent, reusable record of what "good UX" looks like for a given product.

---

## Solution

KayaFlow is a Telegram bot that acts as an always-on AI UX kaki (buddy). Upload a screenshot, get immediate actionable feedback in conversational Singapore English. Over time, approved patterns accumulate into a structured design memory library your whole team can reference.

---

## Target Users

- **Primary**: Product designers and PMs building consumer fintech/SaaS in Singapore/SEA
- **Secondary**: Founders doing their own UX reviews
- **Out of scope**: Enterprise design systems teams (different tool category)

---

## Success Metrics (V1)

| Metric | Target |
|---|---|
| Time to first feedback | < 15 seconds |
| Pattern approvals per week | > 5 (active user) |
| Follow-up question rate | > 40% of sessions |
| Design memory patterns saved | 20+ after 30 days |

---

## User Stories

### Core Flow

**US-001**: As a designer, I can send a screenshot to the KayaFlow Telegram bot and receive UX feedback within 15 seconds.

**US-002**: As a designer, I can receive feedback that acknowledges where this screen sits in the customer journey (onboarding, KYC, checkout, etc.).

**US-003**: As a designer, I can reply to KayaFlow's feedback with follow-up questions and get contextual responses.

**US-004**: As a designer, I can approve a UX pattern that KayaFlow identifies and have it saved to the design memory library.

**US-005**: As a designer, I can use `/patterns` to see saved patterns by category.

### Memory & Context

**US-006**: As a designer, KayaFlow uses previously saved patterns to give me more relevant feedback on new screens.

**US-007**: As a designer, I can use `/journey` to tag a screen to a specific journey stage before sending for review.

**US-008**: As a designer, I can use `/save` after a review session to save the full session summary as a journey review.

### Commands

**US-009**: `/start` — Welcome message, explain how to use KayaFlow
**US-010**: `/help` — List all commands
**US-011**: `/patterns [category]` — List saved patterns
**US-012**: `/approve` — Approve last suggested pattern for saving
**US-013**: `/journey [stage]` — Set journey context for next upload
**US-014**: `/save` — Save current session as journey review
**US-015**: `/feedback` — Give feedback on KayaFlow's analysis quality

---

## Technical Requirements

### Performance
- UX critique response: < 15 seconds (Claude API + image processing)
- Bot availability: 99%+ (polling mode for V1, webhook for V2)
- Memory store: < 100ms read for pattern retrieval

### Image Handling
- Accept: JPEG, PNG, WebP (Telegram-native formats)
- Max size: 20MB (Telegram limit)
- OCR: Optional enhancement, graceful fallback if pytesseract unavailable

### Memory
- V1: JSON file store, human-readable, GitHub-committable
- V2: SQLite for scale (> 500 patterns)
- Pattern format: YAML in `design-memory/` (version-controlled)

### Security
- API keys via environment variables only
- No PII stored in design memory
- Screenshots processed in memory, not persisted to disk

---

## Journey Categories (V1)

| Category | Description |
|---|---|
| `onboarding` | First-time user flows, sign-up screens |
| `kyc` | Identity verification, document upload |
| `trust-signals` | Social proof, security badges, guarantees |
| `cta-patterns` | Call-to-action buttons, forms, conversion points |
| `navigation` | Menus, tabs, back navigation, wayfinding |
| `anti-patterns` | Dark patterns, confusion points, friction |

---

## V1 Scope (Must Have)

- [x] Telegram bot with photo message handling
- [x] Claude-powered UX critique
- [x] Journey context detection
- [x] Multi-turn conversation state
- [x] Pattern approval flow
- [x] JSON memory store
- [x] YAML pattern files in design-memory/
- [x] OCR extraction (with graceful fallback)
- [x] `/start`, `/help`, `/patterns`, `/approve` commands

## V2 Scope (Later)

- [ ] Webhook mode for production deployment
- [ ] SQLite memory store upgrade
- [ ] Pattern similarity search (vector embeddings)
- [ ] Team sharing via shared Telegram group
- [ ] GitHub auto-commit for approved patterns
- [ ] Figma plugin integration
- [ ] Web dashboard for design memory browsing

---

## Open Questions

1. Should KayaFlow support group chats for team reviews? (V2 scope candidate)
2. How do we handle screen flows (multiple related screenshots)? Suggest user send in sequence with `/flow` command.
3. Rate limiting: per-user per-day limits needed to control API costs?

---

## Dependencies

| Dependency | Version | Purpose |
|---|---|---|
| python-telegram-bot | 21.x | Telegram bot framework |
| anthropic | 0.25+ | Claude API |
| pytesseract | 0.3.x | OCR (optional) |
| Pillow | 10.x | Image processing |
| pydantic | 2.x | Data validation |
| python-dotenv | 1.x | Environment config |
| pyyaml | 6.x | Pattern file storage |
| pytest | 8.x | Testing |
