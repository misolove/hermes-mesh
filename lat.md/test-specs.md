# Test Specs

Test specs describe the behavioral checks that should protect memory provenance, approval policy, daemon auth, and sync safety.

## Memory Card Validation Spec

require-code-mention: true

Memory-card tests should prove that anonymous or empty shared memories cannot enter the registry. At minimum, tests should cover non-empty source fields, non-empty subject/title/content, stable ID generation, and secret/dangerous confirmation behavior.

Implementation anchors:

- [[src/hermes_mesh/memory.py#MemoryCard]]
- [[src/hermes_mesh/memory.py#stable_memory_id]]

## Registry Approval Spec

require-code-mention: true

Registry tests should prove that proposing an existing card is idempotent, state-filtered listing works, approvals/rejections require an actor, and decision audit events are appended.

Implementation anchor: [[src/hermes_mesh/registry.py#MemoryRegistry]]

## Daemon Auth And Sync API Spec

require-code-mention: true

Daemon tests should prove that protected endpoints reject missing or invalid bearer tokens when configured, public endpoints remain reachable, inbound sync imports only approved shared cards, and pull returns only approved shared cards.

Implementation anchors:

- [[src/hermes_mesh/daemon.py#create_app]]
- [[src/hermes_mesh/daemon.py#unauthorized]]
- [[src/hermes_mesh/sync.py#import_approved_cards]]

## Sync Loop Spec

require-code-mention: true

Sync-loop tests should prove that each peer receives heartbeat, approved-card push, pull, and local import in order, and that heartbeat failures are reported without crashing the loop.

Implementation anchors:

- [[src/hermes_mesh/sync.py#MemorySyncClient]]
- [[src/hermes_mesh/sync.py#run_sync_once]]
