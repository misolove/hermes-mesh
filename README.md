# hermes-mesh

[한국어 README](README.ko.md)

Hermes Mesh is a personal agent control-plane concept for letting Hermes instances and machine-local tool nodes cooperate safely across a private network such as Tailscale.

The immediate target is Lerippi's environment:

- Controller: MacBook M3 Max running Hermes Agent
- Remote node: Ubuntu `mail` server running website and mail services
- Transport: Tailscale private network
- Tool protocol: MCP over HTTP
- Operating model: policy-bound tools, audit logs, backups, and explicit approval for dangerous actions

## What this project is

`hermes-mesh` aims to make remote machines first-class, safe tools for Hermes.

Instead of giving an agent unrestricted SSH/root access, each machine runs a small policy-enforced node service that exposes a limited MCP tool surface:

- system diagnostics
- safe command execution through allowlists
- file reads/writes with path policy and backups
- git/deploy workflows
- web service checks/reloads
- mail server diagnostics
- optional remote Hermes delegation

## Target architecture

```text
MacBook Hermes Controller
  |
  | MCP over HTTP + Bearer token
  | Tailscale private DNS/IP only
  v
Ubuntu hermes-node-mcp
  - policy engine
  - tool handlers
  - audit log
  - optional sudo wrapper scripts
  - optional local Hermes worker
```

## Repository status

This repo currently contains the initial architecture, threat model, MVP plan, MCP tool spec, configs, and skill drafts. Implementation will follow the staged plan in `docs/mvp.md`.

## Reading order

1. `docs/architecture.md`
2. `docs/threat-model.md`
3. `docs/mvp.md`
4. `docs/mcp-tools.md`
5. `configs/node.example.yaml`
6. `skills/hermes-mesh-control/SKILL.md`
7. `skills/ubuntu-mail-homepage-admin/SKILL.md`
8. `skills/remote-hermes-delegation/SKILL.md`

## Non-goals

- Do not expose remote control over the public internet.
- Do not run the node service as root.
- Do not provide unrestricted shell/root access as an MCP tool.
- Do not store real tokens, private keys, or production secrets in this repo.

## License

MIT, unless changed later.
