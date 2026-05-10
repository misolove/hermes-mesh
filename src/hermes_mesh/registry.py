"""Local file-backed registry for shared-memory proposals."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hermes_mesh.memory import MemoryCard, PromotionState


class MemoryRegistry:
    """Store memory cards and approval decisions in a local registry directory."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.cards_dir = self.root / "memory-cards"
        self.decisions_path = self.root / "decisions.jsonl"
        self.cards_dir.mkdir(parents=True, exist_ok=True)

    def propose(self, card: MemoryCard) -> MemoryCard:
        existing = self.get(card.id, missing_ok=True)
        if existing is not None:
            return existing
        self._write_card(card)
        return card

    def get(self, memory_id: str | None, *, missing_ok: bool = False) -> MemoryCard | None:
        if not memory_id:
            if missing_ok:
                return None
            raise ValueError("memory_id is required")
        path = self._card_path(memory_id)
        if not path.exists():
            if missing_ok:
                return None
            raise KeyError(f"memory card not found: {memory_id}")
        return MemoryCard.model_validate_json(path.read_text(encoding="utf-8"))

    def list_cards(self, *, state: str | PromotionState | None = None) -> list[MemoryCard]:
        cards = [
            MemoryCard.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.cards_dir.glob("mem_*.json"))
        ]
        if state is None:
            return cards
        state_value = state.value if isinstance(state, PromotionState) else state
        return [card for card in cards if card.promotion.state.value == state_value]

    def approve(self, memory_id: str, *, actor: str, reason: str | None = None) -> MemoryCard:
        card = self._decide(
            memory_id,
            state=PromotionState.APPROVED_SHARED,
            actor=actor,
            reason=reason,
            actor_field="approved_by",
        )
        self._append_decision("approve", card, actor=actor, reason=reason)
        return card

    def reject(self, memory_id: str, *, actor: str, reason: str | None = None) -> MemoryCard:
        card = self._decide(
            memory_id,
            state=PromotionState.REJECTED,
            actor=actor,
            reason=reason,
            actor_field="rejected_by",
        )
        self._append_decision("reject", card, actor=actor, reason=reason)
        return card

    def _decide(
        self,
        memory_id: str,
        *,
        state: PromotionState,
        actor: str,
        reason: str | None,
        actor_field: str,
    ) -> MemoryCard:
        if not actor.strip():
            raise ValueError("actor must be non-empty")
        card = self.get(memory_id)
        assert card is not None
        card.promotion.state = state
        card.promotion.decided_at = datetime.now(UTC)
        card.promotion.reason = reason
        setattr(card.promotion, actor_field, actor)
        self._write_card(card)
        return card

    def _write_card(self, card: MemoryCard) -> None:
        path = self._card_path(card.id)
        path.write_text(
            json.dumps(card.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _append_decision(
        self, action: str, card: MemoryCard, *, actor: str, reason: str | None = None
    ) -> None:
        self.decisions_path.parent.mkdir(parents=True, exist_ok=True)
        event: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "action": action,
            "memory_id": card.id,
            "actor": actor,
            "state": card.promotion.state.value,
        }
        if reason:
            event["reason"] = reason
        with self.decisions_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    def _card_path(self, memory_id: str | None) -> Path:
        if not memory_id:
            raise ValueError("memory_id is required")
        return self.cards_dir / f"{memory_id}.json"
