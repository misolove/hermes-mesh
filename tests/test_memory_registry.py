import json

from hermes_mesh.memory import MemoryCard
from hermes_mesh.registry import MemoryRegistry


def valid_card_data(**overrides):
    data = {
        "subject": "ubuntu-mail-node",
        "title": "Ubuntu mail node is reachable over Tailscale",
        "content": "The Ubuntu server is reachable as mail.tailb30d36.ts.net.",
        "source": {
            "node_id": "macbook-controller",
            "agent": "hermes",
            "method": "tailscale_status",
            "observed_at": "2026-05-10T15:30:00+09:00",
            "evidence": [{"type": "command", "command": "tailscale status --json", "redacted": True}],
        },
        "confidence": "high",
        "sensitivity": "low",
    }
    data.update(overrides)
    return data


def test_registry_proposes_memory_card_and_persists_source(tmp_path):
    registry = MemoryRegistry(tmp_path)
    card = MemoryCard.model_validate(valid_card_data())

    saved = registry.propose(card)
    loaded = registry.get(saved.id)

    assert loaded.id == saved.id
    assert loaded.source.node_id == "macbook-controller"
    assert loaded.source.method == "tailscale_status"
    assert (tmp_path / "memory-cards" / f"{saved.id}.json").exists()


def test_registry_deduplicates_same_card_id(tmp_path):
    registry = MemoryRegistry(tmp_path)
    card = MemoryCard.model_validate(valid_card_data())

    first = registry.propose(card)
    second = registry.propose(card)

    assert first.id == second.id
    assert len(registry.list_cards()) == 1


def test_registry_approve_and_reject_record_decisions(tmp_path):
    registry = MemoryRegistry(tmp_path)
    card = registry.propose(MemoryCard.model_validate(valid_card_data()))

    approved = registry.approve(card.id, actor="lerippi", reason="trusted node fact")
    rejected = registry.reject(card.id, actor="lerippi", reason="superseded")

    assert approved.promotion.state.value == "approved_shared"
    assert rejected.promotion.state.value == "rejected"
    decisions = (tmp_path / "decisions.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert [json.loads(line)["action"] for line in decisions] == ["approve", "reject"]
    assert json.loads(decisions[0])["memory_id"] == card.id


def test_registry_filters_by_state(tmp_path):
    registry = MemoryRegistry(tmp_path)
    card1 = registry.propose(MemoryCard.model_validate(valid_card_data(title="A", content="A")))
    card2 = registry.propose(MemoryCard.model_validate(valid_card_data(title="B", content="B")))
    registry.approve(card1.id, actor="lerippi")

    proposed = registry.list_cards(state="proposed")
    approved = registry.list_cards(state="approved_shared")

    assert [card.id for card in proposed] == [card2.id]
    assert [card.id for card in approved] == [card1.id]
