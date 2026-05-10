from pathlib import Path

from starlette.testclient import TestClient

from hermes_mesh.daemon import create_app
from hermes_mesh.memory import MemoryCard


def valid_card_data(**overrides):
    data = {
        "subject": "ubuntu-mail-node",
        "title": "Ubuntu mail node is reachable over Tailscale",
        "content": "The Ubuntu server is reachable as mail.tailb30d36.ts.net.",
        "source": {
            "node_id": "ubuntu-mail",
            "agent": "hermes-mesh-daemon",
            "method": "system_probe",
            "observed_at": "2026-05-10T15:30:00+09:00",
            "evidence": [{"type": "probe", "redacted": True}],
        },
        "confidence": "high",
        "sensitivity": "low",
    }
    data.update(overrides)
    return data


def make_client(tmp_path: Path, *, node_id="macbook-controller", token="secret"):
    app = create_app(registry_root=tmp_path, node_id=node_id, token=token)
    return TestClient(app)


def auth(token="secret"):
    return {"Authorization": f"Bearer {token}"}


def test_health_and_node_metadata_are_public(tmp_path):
    client = make_client(tmp_path)

    assert client.get("/health").json() == {"ok": True}
    node = client.get("/node").json()

    assert node["node_id"] == "macbook-controller"
    assert node["role"] == "controller"


def test_memory_propose_requires_bearer_token(tmp_path):
    client = make_client(tmp_path)

    response = client.post("/memory/propose", json=valid_card_data())

    assert response.status_code == 401


def test_memory_propose_rejects_missing_source(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/memory/propose",
        headers=auth(),
        json={"subject": "x", "title": "x", "content": "x"},
    )

    assert response.status_code == 422
    assert "source" in response.text


def test_memory_propose_list_approve_roundtrip(tmp_path):
    client = make_client(tmp_path)

    proposed = client.post("/memory/propose", headers=auth(), json=valid_card_data())
    assert proposed.status_code == 200, proposed.text
    memory_id = proposed.json()["id"]
    assert proposed.json()["source"]["node_id"] == "ubuntu-mail"

    listed = client.get("/memory/cards", headers=auth(), params={"state": "proposed"})
    assert listed.status_code == 200, listed.text
    assert [item["id"] for item in listed.json()] == [memory_id]

    approved = client.post(
        f"/memory/cards/{memory_id}/approve",
        headers=auth(),
        json={"actor": "lerippi", "reason": "trusted source"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["promotion"]["state"] == "approved_shared"


def test_memory_sync_push_accepts_only_approved_cards(tmp_path):
    client = make_client(tmp_path)

    proposed = client.post("/memory/propose", headers=auth(), json=valid_card_data()).json()
    memory_id = proposed["id"]
    client.post(f"/memory/cards/{memory_id}/approve", headers=auth(), json={"actor": "lerippi"})

    other_proposed = valid_card_data(title="unapproved", content="unapproved")
    response = client.post(
        "/memory/sync/push",
        headers=auth(),
        json={"cards": [proposed, other_proposed], "from_node": "ubuntu-mail"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["accepted"] == []
    expected_other_id = MemoryCard.model_validate(other_proposed).id
    assert body["skipped"] == [proposed["id"], expected_other_id]
