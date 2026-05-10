from starlette.testclient import TestClient

from hermes_mesh.daemon import create_app
from hermes_mesh.memory import MemoryCard


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


def auth():
    return {"Authorization": "Bearer secret"}


def test_heartbeat_endpoint_requires_auth_and_returns_node(tmp_path):
    client = TestClient(create_app(registry_root=tmp_path, node_id="macbook", token="secret"))

    assert client.post("/peers/heartbeat").status_code == 401
    response = client.post("/peers/heartbeat", headers=auth(), json={"from_node": "ubuntu"})

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["node_id"] == "macbook"
    assert response.json()["from_node"] == "ubuntu"


def test_sync_pull_returns_approved_shared_cards_only(tmp_path):
    client = TestClient(create_app(registry_root=tmp_path, node_id="macbook", token="secret"))
    proposed = client.post("/memory/propose", headers=auth(), json=valid_card_data()).json()
    client.post(f"/memory/cards/{proposed['id']}/approve", headers=auth(), json={"actor": "lerippi"})
    client.post(
        "/memory/propose",
        headers=auth(),
        json=valid_card_data(title="pending", content="pending"),
    )

    response = client.get("/memory/sync/pull", headers=auth(), params={"from_node": "ubuntu"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert [card["id"] for card in body["cards"]] == [proposed["id"]]
    assert MemoryCard.model_validate(body["cards"][0]).promotion.state.value == "approved_shared"
