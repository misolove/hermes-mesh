# Hermes Mesh Architecture

## Goal

Allow Hermes instances and Hermes-compatible machine nodes to communicate over a private network, so one Hermes can safely inspect, operate, and delegate work to another machine.

The first concrete use case is:

```text
MacBook Hermes controls Ubuntu mail/homepage server over Tailscale.
```

## Layers

```text
Interaction Layer
  - User asks local Hermes for remote server work
  - Telegram/Discord/CLI can later become entry points

Controller Layer
  - MacBook Hermes plans, reviews, and coordinates
  - Loads skills that encode remote-operation policy

Transport Layer
  - Tailscale private network
  - Optional Tailscale ACLs
  - HTTP MCP endpoint bound to Tailscale IP/DNS only

Tool Layer
  - Remote MCP server exposes typed tools
  - Tools are policy-bound and audited

Execution Layer
  - Ubuntu local shell commands
  - sudo wrapper scripts for restricted privileged actions
  - Git deploy scripts
  - service status/reload scripts

Delegation Layer, optional
  - Remote Hermes can be invoked for local analysis or long-running jobs
  - Controller Hermes remains final reviewer for risky changes
```

## Component diagram

```mermaid
flowchart TD
    U[User] --> H1[MacBook Hermes Controller]
    H1 --> S1[hermes-mesh-control skill]
    H1 --> S2[ubuntu-mail-homepage-admin skill]
    H1 --> MCP[MCP Client]
    MCP -->|HTTP over Tailscale + Bearer| NODE[Ubuntu hermes-node-mcp]
    NODE --> POL[Policy Engine]
    NODE --> AUD[Audit Log JSONL]
    POL --> SYS[System Tools]
    POL --> FS[File Tools]
    POL --> GIT[Git/Deploy Tools]
    POL --> WEB[Nginx/Web Tools]
    POL --> MAIL[Postfix/Dovecot Tools]
    POL --> RH[Remote Hermes Tools]
    WEB --> SUDO[Sudo Wrapper Scripts]
    MAIL --> SUDO
    RH --> H2[Ubuntu Hermes Worker]
```

## Request flow

```mermaid
sequenceDiagram
    participant User
    participant Local as MacBook Hermes
    participant Skill as Mesh Skills
    participant MCP as Ubuntu MCP Node
    participant OS as Ubuntu OS

    User->>Local: 홈페이지 상태 확인해줘
    Local->>Skill: Load remote operation rules
    Local->>MCP: homepage_status()
    MCP->>MCP: Check auth and policy
    MCP->>OS: git status, nginx status, curl local health
    OS-->>MCP: outputs
    MCP->>MCP: Write audit log
    MCP-->>Local: structured result
    Local-->>User: 요약 + next actions
```

## Responsibility split

| Component | Responsibility | Should not do |
| --- | --- | --- |
| MacBook Hermes | plan, decide, review, ask approval | hold server root keys unrestricted |
| Mesh skill | operational policy and workflows | store secrets |
| MCP node | expose safe typed tools | make autonomous high-risk decisions |
| Policy engine | allow/deny paths/commands/services | trust model output blindly |
| Sudo wrappers | narrow privileged actions | expose `sudo ALL` |
| Audit log | record remote actions | store secret arguments verbatim |
| Remote Hermes | optional local reasoning | bypass controller approval |

## Recommended node roles

```yaml
roles:
  - controller
  - desktop
  - webserver
  - mailserver
  - deploy-target
  - gpu-worker
  - nas
  - knowledge-base
```

## First production target

```yaml
node:
  id: ubuntu-mail
  host: mail.tailb30d36.ts.net
  tailscale_ip: 100.89.252.12
  roles: [webserver, mailserver, deploy-target]
services:
  - nginx
  - postfix
  - dovecot
  - certbot
```
