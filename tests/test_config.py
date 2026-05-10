from pathlib import Path

from hermes_mesh.config import DaemonConfig, load_daemon_config


def test_load_daemon_config_resolves_env_tokens(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PEER_TOKEN", "peer-secret")
    config_path = tmp_path / "node.yaml"
    config_path.write_text(
        """
node:
  id: macbook-controller
  role: controller
server:
  host: 127.0.0.1
  port: 8732
registry:
  path: /tmp/hermes-mesh-registry
sync:
  heartbeat_interval_seconds: 10
  sync_interval_seconds: 20
peers:
  - id: ubuntu-mail
    url: http://100.89.252.12:8732
    token_env: PEER_TOKEN
""".strip(),
        encoding="utf-8",
    )

    config = load_daemon_config(config_path)

    assert config.node.id == "macbook-controller"
    assert config.node.role == "controller"
    assert config.server.port == 8732
    assert config.peers[0].token == "peer-secret"
    assert config.sync.heartbeat_interval_seconds == 10


def test_daemon_config_rejects_peer_without_token():
    try:
        DaemonConfig.model_validate(
            {
                "node": {"id": "macbook"},
                "peers": [{"id": "ubuntu", "url": "http://ubuntu:8732"}],
            }
        )
    except ValueError as exc:
        assert "token" in str(exc)
    else:
        raise AssertionError("expected config validation failure")
