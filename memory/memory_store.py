import json
import logging
from pathlib import Path

import yaml

from config.settings import MEMORY_STORE_PATH, DESIGN_MEMORY_PATH
from memory.pattern_schema import UXPattern

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Dual-layer storage:
    - JSON index at MEMORY_STORE_PATH (fast lookups, metadata)
    - YAML files in DESIGN_MEMORY_PATH/<category>/ (human-readable, git-friendly)
    """

    def __init__(
        self,
        store_path: Path = MEMORY_STORE_PATH,
        design_memory_path: Path = DESIGN_MEMORY_PATH,
    ) -> None:
        self.store_path = store_path
        self.design_memory_path = design_memory_path
        self._ensure_paths()
        self._index: dict[str, dict] = self._load_index()

    def _ensure_paths(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.design_memory_path.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> dict[str, dict]:
        if not self.store_path.exists():
            return {}
        try:
            with open(self.store_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not load memory index: {e}")
            return {}

    def _save_index(self) -> None:
        with open(self.store_path, "w") as f:
            json.dump(self._index, f, indent=2)

    def save_pattern(self, pattern: UXPattern) -> None:
        """Save pattern to JSON index and YAML file."""
        # Update index
        self._index[pattern.pattern_id] = pattern.model_dump()
        self._save_index()

        # Write YAML to design-memory/<category>/
        category_dir = self.design_memory_path / pattern.category
        category_dir.mkdir(exist_ok=True)
        yaml_path = category_dir / pattern.filename()
        with open(yaml_path, "w") as f:
            yaml.dump(
                pattern.to_yaml_dict(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        logger.info(f"Saved pattern YAML: {yaml_path}")

    def get_patterns_by_category(self, category: str) -> list[UXPattern]:
        """Return all patterns for a given category, sorted by approval date."""
        patterns = [
            UXPattern(**v)
            for v in self._index.values()
            if v.get("category") == category
        ]
        return sorted(patterns, key=lambda p: p.approved_at, reverse=True)

    def get_all_patterns(self) -> list[UXPattern]:
        return [UXPattern(**v) for v in self._index.values()]

    def count(self) -> int:
        return len(self._index)

    def get_recent(self, n: int = 5) -> list[UXPattern]:
        patterns = self.get_all_patterns()
        return sorted(patterns, key=lambda p: p.approved_at, reverse=True)[:n]
