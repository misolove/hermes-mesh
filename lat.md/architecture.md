# Architecture

Hermes Mesh separates repo concepts into small linked architecture notes that agents can resolve without rereading the whole codebase.

## Mesh Planes

Hermes Mesh uses distinct planes so one Hermes instance can operate remote machines without turning private memory or raw credentials into ambient shared context.

The current repository follows this plane split from README.md “What is this?”:

- Coordination plane: Discord, Telegram, and CLI entry points.
- Execution plane: Hermes Mesh MCP nodes and daemon APIs.
- Shared memory plane: source-attributed `MemoryCard` records in a local registry.
- Skill sharing plane: future user-confirmed skill packages.
- Durable knowledge plane: Boradori and Obsidian.
- Source-of-truth plane: GitHub.

Implementation anchors:

- [[src/hermes_mesh/daemon.py#create_app]] exposes the daemon HTTP surface.
- [[src/hermes_mesh/mcp_facade.py#DaemonClient]] keeps MCP thin by delegating to the daemon.
- [[src/hermes_mesh/cli.py#build_parser]] provides a human/debug/admin surface for the local registry.

## Daemon First Runtime

Automatic memory exchange belongs in an always-on daemon, not inside transient MCP tool calls.

MCP remains the agent-facing control surface, while the daemon performs heartbeat, inbound proposal handling, approved-card sync, retries, and registry writes. The runtime split is documented in docs/daemon-sync.md “Why daemon first” and implemented by:

- [[src/hermes_mesh/daemon.py#create_app]] for Starlette routes and optional periodic sync.
- [[src/hermes_mesh/sync.py#run_sync_once]] for heartbeat, push, pull, and import orchestration.
- [[src/hermes_mesh/mcp_facade.py#DaemonClient]] for local MCP-to-daemon access.

## Security Boundary

Protected daemon endpoints use bearer-token checks, while `/health` and `/node` are public for lightweight peer discovery. Config defaults bind servers to localhost unless explicit config changes the host.

Anchors:

- [[src/hermes_mesh/daemon.py#unauthorized]] defines bearer-token enforcement.
- [[src/hermes_mesh/config.py#ServerConfig]] defaults daemon host and token lookup.
- [[src/hermes_mesh/config.py#PeerConfig]] requires enabled peers to have a token or `token_env`.
