# Shared Memory

Shared memory notes define what can be shared across Hermes nodes, how provenance is preserved, and when approval is required.

## Source Attributed Memory Cards

A shared memory is never an anonymous sentence. Every shared fact must carry provenance so a receiving Hermes can distinguish imported knowledge from direct observation.

The executable schema lives in [[src/hermes_mesh/memory.py#MemoryCard]] and requires:

- `subject`, `title`, and `content` as non-empty text.
- `source` with node, agent, method, timestamp, and optional redacted evidence.
- `confidence` and `sensitivity` labels.
- `promotion` state and decision metadata.
- optional `scope` and `links` for policy and cross-system references.

The source preservation rule is also described in docs/daemon-sync.md “Source preservation rule”.

## Promotion Policy

Memory sharing follows the project principle from docs/shared-memory-and-skills.md “Core principle”: automatic propose, explicit provenance, user-approved promotion.

Current promotion states are defined by [[src/hermes_mesh/memory.py#PromotionState]]:

- `local_only`: raw private memory, never shared automatically.
- `proposed`: a node thinks the memory may be useful.
- `shared_candidate`: normalized candidate waiting for approval or policy.
- `approved_shared`: canonical shared memory that may sync to peers.
- `rejected`: retained rejection to avoid repeated proposals.
- `expired`: time-bound memory that is no longer current.

[[src/hermes_mesh/memory.py#MemoryCard]] intentionally refuses automatic promotion for `internal`, `secret`, and `dangerous` cards via `can_auto_promote`. `secret` and `dangerous` cards always require user confirmation during validation.

## Local Registry Contract

[[src/hermes_mesh/registry.py#MemoryRegistry]] is the source-attributed truth store for the MVP. It writes memory cards under `memory-cards/` and appends approval/rejection decisions to `decisions.jsonl`.

Registry invariants:

- proposing an existing card is idempotent and returns the existing record;
- listing can filter by promotion state;
- approvals and rejections require a non-empty actor;
- every decision is written as a JSONL audit event;
- card filenames are based on deterministic `mem_*` IDs from [[src/hermes_mesh/memory.py#stable_memory_id]];
- explicit or inbound IDs must match the safe `mem_<16 lowercase hex>` shape enforced by [[src/hermes_mesh/memory.py#validate_memory_id]].
