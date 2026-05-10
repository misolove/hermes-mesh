from pathlib import Path

from hermes_mesh.memory import MemoryCard
from hermes_mesh.registry import MemoryRegistry
from hermes_mesh.sync import MemorySyncClient, run_sync_once


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
            "evidence": [{"type": "command", "redacted": True}],
        },
        "confidence": "high",
        "sensitivity": "low",
    }
    data.update(overrides)
    return data


class FakeTransport:
    def __init__(self):
        self.gets = []
        self.posts = []
        self.pull_response = {"cards": []}
        self.post_response = {"accepted": [], "skipped": []}
        self.health_response = {"ok": True}

    def get_json(self, url, *, token=None, timeout=30):
        self.gets.append({"url": url, "token": token, "timeout": timeout})
        if url.endswith("/health"):
            return self.health_response
        if "/memory/sync/pull" in url:
            return self.pull_response
        return {}

    def post_json(self, url, *, token, payload, timeout):
        self.posts.append({"url": url, "token": token, "payload": payload, "timeout": timeout})
        return self.post_response


def test_run_sync_once_heartbeats_pushes_and_pulls(tmp_path: Path):
    registry = MemoryRegistry(tmp_path)
    local = registry.propose(MemoryCard.model_validate(valid_card_data()))
    registry.approve(local.id, actor="lerippi")
    remote_card = MemoryCard.model_validate(
        valid_card_data(
            title="Remote approved memory",
            content="Remote approved memory",
            source={
                "node_id": "ubuntu-mail",
                "agent": "hermes-mesh-daemon",
                "method": "peer_sync",
                "observed_at": "2026-05-10T15:30:00+09:00",
                "evidence": [{"type": "remote", "redacted": True}],
            },
            promotion={"state": "approved_shared", "requires_user_confirmation": True},
        )
    )
    transport = FakeTransport()
    transport.pull_response = {"cards": [remote_card.to_json_dict()]}
    client = MemorySyncClient("http://ubuntu:8732", token="peer-token", transport=transport)

    result = run_sync_once(registry, [client], from_node="macbook-controller")

    assert result["peers"][0]["heartbeat"]["ok"] is True
    assert result["peers"][0]["push"] == {"accepted": [], "skipped": []}
    assert result["peers"][0]["pull"]["accepted"] == [remote_card.id]
    assert registry.get(remote_card.id).source.node_id == "ubuntu-mail"
    assert any(call["url"] == "http://ubuntu:8732/health" for call in transport.gets)
    assert any("/memory/sync/pull" in call["url"] for call in transport.gets)
    assert any(call["url"] == "http://ubuntu:8732/memory/sync/push" for call in transport.posts)
