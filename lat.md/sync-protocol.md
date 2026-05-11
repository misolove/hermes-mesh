# Sync Protocol

Sync protocol notes define how peers exchange only approved shared memory while preserving source attribution and auditability.

## Push Pull Loop

Peer synchronization is deliberately small and auditable. [[src/hermes_mesh/sync.py#run_sync_once]] loops over configured peers and performs:

1. heartbeat to `/health` and `/peers/heartbeat`,
2. push of locally `approved_shared` cards,
3. pull of remote `approved_shared` cards,
4. import of only valid `approved_shared` cards into the local registry.

The design keeps proposed memories from becoming shared truth merely because a worker pushed them. This is documented in docs/daemon-sync.md “Current sync behavior”.

The daemon exposes `POST /memory/sync/run-once` for controller-initiated sync. It calls [[src/hermes_mesh/sync.py#run_sync_once]] and returns `{"peers": [...]}`; bad peers are reported as structured `ok: false` entries instead of aborting the loop.

## Transport Contract

[[src/hermes_mesh/sync.py#JsonTransport]] defines the transport protocol used by sync clients and the MCP facade. [[src/hermes_mesh/sync.py#UrllibJsonTransport]] is dependency-free and uses bearer-token authorization when a token is supplied.

The narrow transport interface makes sync and facade behavior easy to test with fake transports.

## Peer Client

[[src/hermes_mesh/sync.py#MemorySyncClient]] wraps peer endpoints:

- `heartbeat(from_node=...)` combines public health and authenticated peer heartbeat.
- `push_cards(cards, from_node=...)` sends approved cards to `/memory/sync/push`.
- `pull_cards(from_node=...)` fetches `/memory/sync/pull`.

Heartbeat failures are returned as structured `{ok: false, error: ...}` values so the sync loop can report peer health without crashing.

## Import Rule

[[src/hermes_mesh/sync.py#import_approved_cards]] accepts only `MemoryCard` objects whose promotion state is `approved_shared`. Existing IDs are skipped instead of overwritten.

This prevents inbound peers from silently installing unapproved proposals and preserves source attribution from the original card.
