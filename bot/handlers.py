from __future__ import annotations

import logging

import anthropic
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from config.settings import (
    ANTHROPIC_API_KEY,
    JOURNEY_CATEGORIES,
    JOURNEY_CATEGORY_LABELS,
    OCR_ENABLED,
)
from core.image_intake import download_telegram_photo, preprocess_image, get_best_photo
from core.ocr_extractor import extract_text
from core.journey_context import detect_journey_stage
from core.ux_critique_engine import critique_screenshot, handle_follow_up, handle_casual_chat
from core.conversation_manager import ConversationManager
from core.approval_layer import is_approval_message, approve_and_save_pattern
from memory.hermes_memory import build_memory_context
from memory.memory_store import MemoryStore

logger = logging.getLogger(__name__)

# Secondary review lenses shown per journey stage — reflects what knowledge is actually loaded
_SECONDARY_LENSES: dict[str, str] = {
    "onboarding":    "Trust Signals, Onboarding Psychology, Cognitive Load",
    "kyc":           "Trust Signals, Disclosure Placement, Data Collection Friction",
    "trust-signals": "Disclosure Placement, Product Comprehension, CTA Timing",
    "cta-patterns":  "CTA Timing, Comprehension Gates, Cognitive Load",
    "navigation":    "Cognitive Load, Screen Progression, Wayfinding",
    "anti-patterns": "Trust Signals, Disclosure Placement, Dark Patterns",
}

# Shared state (initialized by telegram_bot.py)
_claude_client: anthropic.AsyncAnthropic | None = None
_conversation_manager: ConversationManager | None = None
_memory_store: MemoryStore | None = None


def init_handlers(
    claude_client: anthropic.AsyncAnthropic,
    conversation_manager: ConversationManager,
    memory_store: MemoryStore,
) -> None:
    global _claude_client, _conversation_manager, _memory_store
    _claude_client = claude_client
    _conversation_manager = conversation_manager
    _memory_store = memory_store


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Eh hello! I'm KayaFlow — your AI UX kaki 👋\n\n"
        "Send me any UI screenshot and I'll give you honest UX feedback, Singapore style.\n\n"
        "Commands:\n"
        "/journey [stage] — tag your screen to a journey stage before uploading\n"
        "/patterns [category] — see saved UX patterns\n"
        "/approve — save the last suggested pattern\n"
        "/help — full command list\n\n"
        "Just send a screenshot to get started lah!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    categories = "\n".join(f"  • {c}" for c in JOURNEY_CATEGORIES)
    await update.message.reply_text(
        "KayaFlow commands:\n\n"
        "/start — welcome message\n"
        "/help — this message\n"
        "/journey [stage] — set journey context for next upload\n"
        f"  Stages: {', '.join(JOURNEY_CATEGORIES)}\n"
        "/patterns — list all saved patterns\n"
        "/patterns [category] — list patterns for a category\n"
        "/approve — approve and save last suggested pattern\n"
        "/clear — clear your conversation history\n\n"
        "Just send a screenshot anytime for a UX review!"
    )


async def journey_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    args = context.args

    if not args:
        categories = "\n".join(f"  • {c} — {JOURNEY_CATEGORY_LABELS[c]}" for c in JOURNEY_CATEGORIES)
        await update.message.reply_text(
            f"Which journey stage?\n\n{categories}\n\n"
            "Example: /journey onboarding"
        )
        return

    stage = args[0].lower()
    if stage not in JOURNEY_CATEGORIES:
        await update.message.reply_text(
            f"Don't know that stage leh. Valid stages:\n"
            + "\n".join(f"  • {c}" for c in JOURNEY_CATEGORIES)
        )
        return

    _conversation_manager.set_journey_stage(user_id, stage)
    label = JOURNEY_CATEGORY_LABELS[stage]
    await update.message.reply_text(
        f"Got it — next screenshot will be reviewed as *{label}* 👍",
        parse_mode="Markdown",
    )


async def patterns_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    category = args[0].lower() if args else None

    if category and category not in JOURNEY_CATEGORIES:
        await update.message.reply_text(
            f"Don't have that category. Try: {', '.join(JOURNEY_CATEGORIES)}"
        )
        return

    if category:
        patterns = _memory_store.get_patterns_by_category(category)
        if not patterns:
            await update.message.reply_text(
                f"No patterns saved for *{JOURNEY_CATEGORY_LABELS[category]}* yet.\n"
                "Send me a screenshot to start building the library!",
                parse_mode="Markdown",
            )
            return
        lines = [f"*{JOURNEY_CATEGORY_LABELS[category]} patterns:*\n"]
        for p in patterns:
            lines.append(f"• *{p.name}*")
            lines.append(f"  {p.description}")
            lines.append(f"  Tags: {', '.join(p.tags)}\n")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    else:
        total = _memory_store.count()
        if total == 0:
            await update.message.reply_text(
                "No patterns saved yet! Send me screenshots and approve patterns to build your design memory library."
            )
            return
        lines = [f"*Design Memory Library* ({total} patterns)\n"]
        for cat in JOURNEY_CATEGORIES:
            cat_patterns = _memory_store.get_patterns_by_category(cat)
            if cat_patterns:
                lines.append(f"• *{JOURNEY_CATEGORY_LABELS[cat]}*: {len(cat_patterns)} patterns")
        lines.append("\nUse /patterns [category] to see details.")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = _conversation_manager.get_or_create(user_id)
    pending = _conversation_manager.pop_pending_pattern(user_id)

    if not pending:
        await update.message.reply_text(
            "Nothing to approve leh. Send me a screenshot first, then I'll suggest a pattern to save."
        )
        return

    await _save_pattern_flow(update, pending, user_id)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    _conversation_manager.clear(user_id)
    await update.message.reply_text("Conversation cleared. Fresh start! Send me a screenshot.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main handler for screenshot uploads."""
    user_id = update.effective_user.id
    session = _conversation_manager.get_or_create(user_id)

    await update.message.chat.send_action(ChatAction.TYPING)

    # Download and preprocess image
    photo = get_best_photo(update.message.photo)
    raw_bytes = await download_telegram_photo(context.bot, photo)
    image_bytes, metadata = preprocess_image(raw_bytes)

    # OCR (optional)
    ocr_text = ""
    if OCR_ENABLED:
        ocr_text = extract_text(image_bytes) or ""

    # Detect journey stage (user hint takes priority)
    journey_stage = await detect_journey_stage(
        _claude_client,
        image_bytes,
        user_hint=session.journey_stage if session.journey_stage != "unknown" else None,
    )
    session.journey_stage = journey_stage

    # Build memory context from past patterns
    memory_context = build_memory_context(_memory_store, journey_stage)

    # Get critique
    feedback, pattern = await critique_screenshot(
        client=_claude_client,
        image_bytes=image_bytes,
        journey_stage=journey_stage,
        memory_context=memory_context,
        ocr_text=ocr_text,
        conversation_history=session.get_history_for_claude(),
    )

    # Update conversation history
    session.add_turn("user", "[screenshot uploaded]")
    session.add_turn("assistant", feedback)

    # Store pending pattern if found
    if pattern:
        _conversation_manager.set_pending_pattern(user_id, pattern)
        footer = f"\n\n💡 *Spotted a pattern:* _{pattern.get('name', 'New Pattern')}_\nReply \"save this\" or /approve to add it to your design library."
    else:
        footer = ""

    await update.message.reply_text(
        feedback + footer,
        parse_mode="Markdown",
    )


_CASUAL_TRIGGERS: frozenset[str] = frozenset({
    # greetings
    "hi", "hello", "hey", "yo", "hiya", "sup", "morning", "good morning",
    "afternoon", "good afternoon", "evening", "good evening",
    # state / feelings
    "how are you", "how are you?", "how r u", "how r u?", "how you doing",
    "how are u", "u ok", "you ok", "you good",
    # capability questions
    "what can you do", "what can you do?", "what do you do", "what do you do?",
    "what are you", "what are you?", "who are you", "who are you?",
    "tell me about yourself", "what is kayaflow", "what's kayaflow",
    "what does kayaflow do", "are you useful", "are you useful?",
    # acknowledgements
    "thanks", "thank you", "thx", "ty", "appreciate it", "appreciated",
    "noted", "got it", "ok", "okay", "cool", "alright", "sure", "nice",
    "good", "great", "ok thanks", "okay thanks", "thanks lah", "ok lah",
})


def is_casual_chat(text: str) -> bool:
    """Return True if the message is casual chat rather than a UX review follow-up."""
    normalized = text.lower().strip().rstrip(".")
    return normalized in _CASUAL_TRIGGERS


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages — casual chat, follow-ups, or approvals."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    session = _conversation_manager.get_or_create(user_id)

    # Check for approval
    if is_approval_message(text):
        pending = _conversation_manager.pop_pending_pattern(user_id)
        if pending:
            await _save_pattern_flow(update, pending, user_id)
            return
        else:
            await update.message.reply_text(
                "No pattern pending leh. Send a screenshot first, then approve the suggested pattern."
            )
            return

    # Casual chat — route to lightweight SG-tone handler regardless of session state
    if is_casual_chat(text):
        await update.message.chat.send_action(ChatAction.TYPING)
        reply = await handle_casual_chat(client=_claude_client, user_message=text)
        await update.message.reply_text(reply)
        return

    # No conversation history — prompt to send a screenshot
    if not session.turns:
        await update.message.reply_text(
            "Send me a screenshot and I'll give you a CX review."
        )
        return

    # Follow-up question in active session
    await update.message.chat.send_action(ChatAction.TYPING)
    response = await handle_follow_up(
        client=_claude_client,
        user_message=text,
        conversation_history=session.get_history_for_claude(),
        journey_stage=session.journey_stage,
    )
    session.add_turn("user", text)
    session.add_turn("assistant", response)
    await update.message.reply_text(response)


async def _save_pattern_flow(update: Update, pattern: dict, user_id: int) -> None:
    """Shared logic for saving an approved pattern."""
    username = update.effective_user.username or ""
    saved = await approve_and_save_pattern(
        store=_memory_store,
        pattern_data=pattern,
        user_id=user_id,
        username=username,
    )
    category_label = JOURNEY_CATEGORY_LABELS.get(saved.category, saved.category)
    await update.message.reply_text(
        f"✅ Saved to design memory!\n\n"
        f"*{saved.name}*\n"
        f"Category: {category_label}\n"
        f"Tags: {', '.join(saved.tags)}\n\n"
        f"It'll come up next time I review a similar screen.",
        parse_mode="Markdown",
    )
