This directory defines high-level concepts, business logic, and architecture for hermes-mesh. It is managed by [lat.md](https://www.npmjs.com/package/lat.md) and anchors source code to these definitions.

- [[architecture]] — Mesh planes, daemon-first runtime, and security boundary.
- [[shared-memory]] — Source-attributed MemoryCard model, promotion policy, and registry contract.
- [[sync-protocol]] — Peer heartbeat, approved-card push/pull, run-once trigger, transport, and import rules.
- [[configuration]] — Daemon, server, peer, and YAML loading configuration contracts.
- [[interfaces]] — CLI, daemon HTTP API, and MCP facade responsibilities.
- [[test-specs]] — Test intent for memory validation, registry decisions, daemon auth, and sync loops.
