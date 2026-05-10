<div align="center">

# hermes-mesh

**A private agent mesh for Hermes-to-machine and Hermes-to-Hermes operations**  
**Hermes들이 안전하게 머신을 조작하고, 기억/스킬을 공유하는 개인 AI 운영망**

<br />

<a href="README.ko.md"><b>한국어로 보기</b></a>
&nbsp;&nbsp;·&nbsp;&nbsp;
<a href="README.en.md"><b>Read in English</b></a>

<br /><br />

<a href="docs/architecture.md">Architecture</a>
&nbsp;·&nbsp;
<a href="docs/threat-model.md">Threat Model</a>
&nbsp;·&nbsp;
<a href="docs/mvp.md">MVP Roadmap</a>
&nbsp;·&nbsp;
<a href="docs/shared-memory-and-skills.md">Memory & Skill Exchange</a>
&nbsp;·&nbsp;
<a href="docs/daemon-sync.md">Daemon Sync</a>

</div>

---

## Quick language select

| Language | Start here | Summary |
| --- | --- | --- |
| 한국어 | [README.ko.md](README.ko.md) | MacBook Hermes가 Ubuntu 홈페이지/메일서버를 Tailscale+MCP로 안전하게 다루고, Hermes들끼리 출처가 명시된 기억과 승인 기반 스킬을 공유하는 구조 |
| English | [README.en.md](README.en.md) | A Tailscale + MCP + policy + audit control plane for safe remote machine control, Hermes-to-Hermes delegation, attributed shared memory, and user-confirmed skill sharing |

## What is this?

`hermes-mesh` is a design-and-implementation project for a personal AI operations mesh.

The first target is Lerippi's setup:

```text
MacBook M3 Max / Hermes Controller
  -> Tailscale private network
  -> Ubuntu `mail` node for homepage + mailserver operations
  -> policy-bound MCP tools, audit logs, backups, and approval gates
```

The larger goal:

```text
Discord / Telegram / CLI = coordination plane
Hermes Mesh MCP nodes    = execution plane
Shared memory cards      = source-attributed memory plane
Skill packages           = user-confirmed skill sharing plane
Boradori / Obsidian      = durable knowledge plane
GitHub                   = source-of-truth plane
```

## Current repository status

This repository currently contains:

- architecture blueprint
- threat model
- MVP roadmap
- MCP tool specification
- shared memory and skill exchange design
- daemon-to-daemon memory sync API
- example node and Hermes configs
- draft Hermes skills
- Python package skeleton for the future MCP node

Implementation is intentionally staged. The first implemented slices are local shared-memory proposals and a daemon HTTP API for node-to-node sync:

```bash
uv run --extra dev hermes-mesh memory propose --file card.json
uv run --extra dev hermes-mesh memory list --state proposed
uv run --extra dev hermes-mesh memory approve mem_xxxxx --actor lerippi
uv run hermes-mesh-daemon --host 127.0.0.1 --port 8732 --node-id macbook-controller --token dev-token
```

The next concrete engineering target is:

```text
MacBook Hermes can call system_info() on the Ubuntu `mail` node over Tailscale MCP.
```

## Reading order

1. [한국어 README](README.ko.md) or [English README](README.en.md)
2. [Architecture](docs/architecture.md)
3. [Threat Model](docs/threat-model.md)
4. [MVP Roadmap](docs/mvp.md)
5. [MCP Tool Specification](docs/mcp-tools.md)
6. [Shared Memory and Skill Exchange](docs/shared-memory-and-skills.md)
7. [Daemon Sync](docs/daemon-sync.md)
8. [Example Ubuntu Node Config](configs/node.example.yaml)
9. [Draft Skills](skills/)

## License

MIT
