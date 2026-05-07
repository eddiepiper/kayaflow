from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from config.settings import MAX_CONVERSATION_HISTORY

logger = logging.getLogger(__name__)


@dataclass
class Turn:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationSession:
    user_id: int
    turns: list[Turn] = field(default_factory=list)
    journey_stage: str = "unknown"
    pending_pattern: dict | None = None  # Pattern awaiting approval
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)

    def add_turn(self, role: str, content: str) -> None:
        self.turns.append(Turn(role=role, content=content))
        self.last_active = datetime.utcnow()
        # Trim history to avoid runaway context
        if len(self.turns) > MAX_CONVERSATION_HISTORY * 2:
            self.turns = self.turns[-MAX_CONVERSATION_HISTORY * 2:]

    def get_history_for_claude(self) -> list[dict]:
        """Return turns formatted for the Claude messages API."""
        return [{"role": t.role, "content": t.content} for t in self.turns]

    def get_context_summary(self) -> str:
        """Short summary of session for follow-up prompts."""
        if not self.turns:
            return "No prior conversation."
        last_assistant = next(
            (t.content for t in reversed(self.turns) if t.role == "assistant"), ""
        )
        return last_assistant[:500] if last_assistant else "No prior feedback."

    def clear(self) -> None:
        self.turns.clear()
        self.pending_pattern = None
        self.journey_stage = "unknown"


class ConversationManager:
    """In-memory conversation state per user. Not persisted across restarts."""

    def __init__(self) -> None:
        self._sessions: dict[int, ConversationSession] = {}

    def get_or_create(self, user_id: int) -> ConversationSession:
        if user_id not in self._sessions:
            self._sessions[user_id] = ConversationSession(user_id=user_id)
            logger.debug(f"New session for user {user_id}")
        return self._sessions[user_id]

    def clear(self, user_id: int) -> None:
        if user_id in self._sessions:
            self._sessions[user_id].clear()

    def set_journey_stage(self, user_id: int, stage: str) -> None:
        session = self.get_or_create(user_id)
        session.journey_stage = stage

    def set_pending_pattern(self, user_id: int, pattern: dict) -> None:
        session = self.get_or_create(user_id)
        session.pending_pattern = pattern

    def pop_pending_pattern(self, user_id: int) -> dict | None:
        session = self.get_or_create(user_id)
        pattern = session.pending_pattern
        session.pending_pattern = None
        return pattern
