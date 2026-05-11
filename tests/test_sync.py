import json
from pathlib import Path

from hermes_mesh.memory import MemoryCard
from hermes_mesh.registry import MemoryRegistry
from hermes_mesh.sync import MemorySyncClient, import_approved_cards, sync_approved_to_peer


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


class FakeTransport:
    def __init__(self):
        self.requests = []
        self.gets = []
        self.response = {"accepted": [], "skipped": []}

    def get_json(self, url, *, token=None, timeout=30):
        self.gets.append({"url": url, "token": token, "timeout": timeout})
        return {"cards": []}

    def post_json(self, url, *, token, payload, timeout):
        self.requests.append({"url": url, "token": token, "payload": payload, "timeout": timeout})
        return self.response


def test_sync_approved_to_peer_sends_only_approved_cards(tmp_path: Path):
    registry = MemoryRegistry(tmp_path)
    approved = registry.propose(MemoryCard.model_validate(valid_card_data()))
    proposed = registry.propose(MemoryCard.model_validate(valid_card_data(title="pending", content="pending")))
    registry.approve(approved.id, actor="lerippi")
    transport = FakeTransport()
    client = MemorySyncClient(
        base_url="http://ubuntu-mail:8732",
        token="peer-token",
        transport=transport,
    )

    result = sync_approved_to_peer(registry, client, from_node="macbook-controller")

    assert result == {"accepted": [], "skipped": []}
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request["url"] == "http://ubuntu-mail:8732/memory/sync/push"
    assert request["token"] == "peer-token"
    assert request["payload"]["from_node"] == "macbook-controller"
    assert [card["id"] for card in request["payload"]["cards"]] == [approved.id]
    assert proposed.id not in json.dumps(request["payload"])


def test_sync_client_normalizes_base_url_and_timeout():
    transport = FakeTransport()
    client = MemorySyncClient("http://node:8732/", token="t", timeout=12, transport=transport)

    client.push_cards([], from_node="macbook")

    assert transport.requests[0]["url"] == "http://node:8732/memory/sync/push"
    assert transport.requests[0]["timeout"] == 12


def test_sync_client_url_encodes_pull_from_node():
    transport = FakeTransport()
    client = MemorySyncClient("http://node:8732/", token="t", transport=transport)

    client.pull_cards(from_node="mac book/controller")

    assert transport.gets[0]["url"] == "http://node:8732/memory/sync/pull?from_node=mac+book%2Fcontroller"


def test_import_approved_cards_skips_malformed_cards_but_keeps_valid_cards(tmp_path: Path):
    registry = MemoryRegistry(tmp_path)
    valid = MemoryCard.model_validate(
        valid_card_data(
            title="Remote approved memory",
            content="Remote approved memory",
            promotion={"state": "approved_shared", "requires_user_confirmation": True},
        )
    ).to_json_dict()
    malformed = {**valid, "id": "../escaped"}

    result = import_approved_cards(registry, [malformed, valid])

    assert result["accepted"] == [valid["id"]]
    assert result["skipped"] == []
    assert result["errors"] and result["errors"][0].startswith("unknown:")
    assert registry.get(valid["id"]).title == "Remote approved memory"
    assert not (tmp_path / "escaped.json").exists()
