import json
import subprocess
import sys
from pathlib import Path


def card_payload_path(tmp_path: Path) -> Path:
    path = tmp_path / "card.json"
    path.write_text(
        json.dumps(
            {
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
        ),
        encoding="utf-8",
    )
    return path


def run_cli(tmp_path: Path, *args: str):
    return subprocess.run(
        [sys.executable, "-m", "hermes_mesh.cli", "--registry", str(tmp_path), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_propose_list_approve_reject_roundtrip(tmp_path):
    payload = card_payload_path(tmp_path)

    proposed = run_cli(tmp_path, "memory", "propose", "--file", str(payload))
    assert proposed.returncode == 0, proposed.stderr
    proposed_data = json.loads(proposed.stdout)
    memory_id = proposed_data["id"]
    assert proposed_data["source"]["node_id"] == "macbook-controller"

    listed = run_cli(tmp_path, "memory", "list", "--state", "proposed")
    assert listed.returncode == 0, listed.stderr
    listed_data = json.loads(listed.stdout)
    assert [item["id"] for item in listed_data] == [memory_id]

    approved = run_cli(tmp_path, "memory", "approve", memory_id, "--actor", "lerippi")
    assert approved.returncode == 0, approved.stderr
    assert json.loads(approved.stdout)["promotion"]["state"] == "approved_shared"

    rejected = run_cli(tmp_path, "memory", "reject", memory_id, "--actor", "lerippi", "--reason", "test")
    assert rejected.returncode == 0, rejected.stderr
    assert json.loads(rejected.stdout)["promotion"]["state"] == "rejected"


def test_cli_rejects_card_without_source(tmp_path):
    payload = tmp_path / "bad.json"
    payload.write_text(json.dumps({"subject": "x", "title": "x", "content": "x"}), encoding="utf-8")

    result = run_cli(tmp_path, "memory", "propose", "--file", str(payload))

    assert result.returncode != 0
    assert "source" in result.stderr
