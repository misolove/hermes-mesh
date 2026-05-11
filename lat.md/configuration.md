# Configuration

Configuration notes define safe daemon defaults, environment-backed secrets, peer validation, and YAML loading behavior.

## Daemon Config Model

[[src/hermes_mesh/config.py#DaemonConfig]] is the configuration root for daemon startup. It composes node identity, server binding/auth, registry location, sync cadence, and peer definitions.

Configuration is intentionally environment-aware but should not require raw secrets in YAML. Token fields can be resolved from environment variables.

## Server Config

[[src/hermes_mesh/config.py#ServerConfig]] defaults to `127.0.0.1:8732` and can resolve `token` from `token_env`.

The localhost default is the safe baseline for development and local MCP wrapping. Remote exposure should happen only through explicit config plus private-network and token controls.

## Peer Config

[[src/hermes_mesh/config.py#PeerConfig]] requires enabled peers to have either `token` or `token_env`. URLs are normalized by stripping trailing slash for HTTP(S) values.

This means a peer entry should fail fast during config validation if it would otherwise create an unauthenticated outbound sync client.

## Loading Config

[[src/hermes_mesh/config.py#load_daemon_config]] reads YAML and validates it through Pydantic before the daemon starts. The daemon consumes this via [[src/hermes_mesh/daemon.py#create_app_from_config]].
