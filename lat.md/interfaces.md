# Interfaces

Interface notes define which surface owns each responsibility: CLI for admin, daemon for runtime, MCP facade for agents.

## CLI Surface

[[src/hermes_mesh/cli.py#build_parser]] exposes the MVP human/debug/admin interface:

- `memory propose --file card.json`
- `memory list --state proposed`
- `memory approve <memory_id> --actor ...`
- `memory reject <memory_id> --actor ...`

The CLI writes directly to [[src/hermes_mesh/registry.py#MemoryRegistry]] and is useful for local smoke tests without starting the daemon.

## Daemon HTTP Surface

[[src/hermes_mesh/daemon.py#create_app]] exposes the Starlette HTTP API. Public endpoints are `/health` and `/node`; memory and sync endpoints are protected when a token is configured.

`/memory/sync/run-once` lets a local controller trigger one immediate peer sync pass and returns the same peer result shape as the background loop. The daemon is the background runtime described in [[architecture#Daemon First Runtime]].

## MCP Facade

[[src/hermes_mesh/mcp_facade.py#DaemonClient]] is intentionally thin. It does not implement synchronization policy; it calls the local daemon for health, node metadata, memory listing, proposal, approval, rejection, and the run-once sync trigger exposed through the MCP `trigger_sync_once` tool.

This keeps MCP tools agent-friendly while preserving the daemon as the operational authority.
