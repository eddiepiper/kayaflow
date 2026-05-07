import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class UXPattern(BaseModel):
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    category: str
    description: str
    context: str = ""
    anti_pattern_if: str = ""
    tags: list[str] = Field(default_factory=list)
    approved_by: str = ""
    approved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    examples: list[str] = Field(default_factory=list)

    def to_yaml_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "category": self.category,
            "tags": self.tags,
            "description": self.description,
            "context": self.context,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "examples": self.examples,
            "anti_pattern_if": self.anti_pattern_if,
        }

    def slug(self) -> str:
        return self.name.lower().replace(" ", "-").replace("/", "-")[:40]

    def filename(self) -> str:
        return f"{self.category}-{self.slug()}-{self.pattern_id}.yaml"
