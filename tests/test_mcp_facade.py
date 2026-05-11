from pathlib import Path

from hermes_mesh.mcp_facade import DaemonClient


class FakeTransport:
    def __init__(self):
        self.gets = []
        self.posts = []

    def get_json(self, url, *, token=None, timeout=30):
        self.gets.append({"url": url, "token": token, "timeout": timeout})
        if url.endswith("/memory/cards?state=proposed") or url.endswith("/memory/cards?state=shared+candidate"):
            return [{"id": "mem_1"}]
        return {"ok": True}

    def post_json(self, url, *, token, payload, timeout):
        self.posts.append({"url": url, "token": token, "payload": payload, "timeout": timeout})
        if url.endswith("/memory/sync/run-once"):
            return {"peers": []}
        return {"id": payload.get("id", "mem_1"), "ok": True}


def test_daemon_client_wraps_memory_tools(tmp_path: Path):
    transport = FakeTransport()
    client = DaemonClient("http://127.0.0.1:8732", token="local-token", transport=transport)

    assert client.health() == {"ok": True}
    assert client.list_memory_cards(state="proposed") == [{"id": "mem_1"}]
    assert client.list_memory_cards(state="shared candidate") == [{"id": "mem_1"}]
    approved = client.approve_memory_card("mem_1", actor="lerippi", reason="ok")

    assert approved["id"] == "mem_1"
    assert transport.gets[0]["url"] == "http://127.0.0.1:8732/health"
    assert transport.gets[1]["url"] == "http://127.0.0.1:8732/memory/cards?state=proposed"
    assert transport.gets[2]["url"] == "http://127.0.0.1:8732/memory/cards?state=shared+candidate"
    assert transport.posts[0]["url"] == "http://127.0.0.1:8732/memory/cards/mem_1/approve"
    assert transport.posts[0]["payload"] == {"actor": "lerippi", "reason": "ok"}


def test_daemon_client_trigger_sync_once_posts_with_token():
    transport = FakeTransport()
    client = DaemonClient("http://127.0.0.1:8732/", token="local-token", transport=transport)

    assert client.trigger_sync_once() == {"peers": []}

    assert transport.posts == [
        {
            "url": "http://127.0.0.1:8732/memory/sync/run-once",
            "token": "local-token",
            "payload": {},
            "timeout": 30,
        }
    ]
