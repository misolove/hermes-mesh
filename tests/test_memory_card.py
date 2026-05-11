import pytest
from pydantic import ValidationError

from hermes_mesh.memory import MemoryCard, PromotionState, Sensitivity


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
            "evidence": [
                {"type": "command", "command": "tailscale status --json", "redacted": True}
            ],
        },
        "confidence": "high",
        "sensitivity": "low",
    }
    data.update(overrides)
    return data


def test_memory_card_requires_explicit_source_provenance():
    data = valid_card_data()
    data.pop("source")

    with pytest.raises(ValidationError) as exc:
        MemoryCard.model_validate(data)

    assert "source" in str(exc.value)


def test_memory_card_requires_non_empty_source_fields():
    data = valid_card_data(source={"node_id": "", "agent": "hermes", "method": "", "observed_at": "2026-05-10T15:30:00+09:00"})

    with pytest.raises(ValidationError) as exc:
        MemoryCard.model_validate(data)

    assert "node_id" in str(exc.value) or "method" in str(exc.value)


def test_memory_card_defaults_to_proposed_promotion_state():
    card = MemoryCard.model_validate(valid_card_data())

    assert card.kind == "memory_card"
    assert card.promotion.state is PromotionState.PROPOSED
    assert card.promotion.requires_user_confirmation is True
    assert card.sensitivity is Sensitivity.LOW
    assert card.source.node_id == "macbook-controller"


def test_memory_card_generates_stable_id_from_content_and_source():
    card1 = MemoryCard.model_validate(valid_card_data())
    card2 = MemoryCard.model_validate(valid_card_data())

    assert card1.id.startswith("mem_")
    assert card1.id == card2.id


def test_secret_memory_cannot_be_auto_promoted():
    card = MemoryCard.model_validate(valid_card_data(sensitivity="secret"))

    assert card.promotion.requires_user_confirmation is True
    assert not card.can_auto_promote()


def test_low_sensitivity_memory_can_auto_promote_when_policy_allows():
    card = MemoryCard.model_validate(valid_card_data(sensitivity="low"))

    assert card.can_auto_promote(auto_promote_low_sensitivity=True)


def test_memory_card_rejects_path_like_or_non_stable_ids():
    for bad_id in ["../escaped", "foo/bar", "/tmp/mem_bad", "mem_nothex"]:
        with pytest.raises(ValidationError):
            MemoryCard.model_validate(valid_card_data(id=bad_id))
