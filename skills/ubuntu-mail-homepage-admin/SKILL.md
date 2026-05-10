---
name: ubuntu-mail-homepage-admin
description: Operate Lerippi's Ubuntu Tailscale node `mail` for homepage and mailserver administration.
version: 0.1.0
author: Lerippi + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ubuntu, tailscale, nginx, postfix, dovecot, homepage, mailserver]
---

# Ubuntu Mail/Homepage Admin

## Node identity

- Tailscale host: `mail.tailb30d36.ts.net`
- Tailscale IPv4 observed: `100.89.252.12`
- Role: homepage server and mail server
- Expected services: nginx, postfix, dovecot, certbot, fail2ban

## Preferred access

Use Hermes Mesh MCP tools when available. Use SSH only as bootstrap/fallback.

## Safe default checks

- system info
- disk/memory
- nginx status
- postfix status
- dovecot status
- recent nginx/postfix/dovecot logs
- TLS certificate expiry
- homepage git status/diff

## Homepage workflow

1. Check repo status.
2. Inspect diff before modifications.
3. Modify only within homepage allowlisted path.
4. Create backup for direct file writes.
5. Run build/test if applicable.
6. Run `nginx -t`.
7. Reload nginx, not restart, unless approved.
8. Health check public/local URL.
9. Report diff and rollback path.

## Mailserver workflow

Default to diagnostics/read-only.

Safe:

- queue inspection
- recent error summary
- service status
- TLS expiry check
- postfix/dovecot reload if policy allows

Approval required:

- account creation/deletion
- mailbox deletion
- postfix/dovecot config edits
- DNS/SPF/DKIM/DMARC changes
- package upgrades
- service restart

## Bootstrap note

Earlier MacBook SSH test saw `ssh mail` reach the host but fail with public key auth for user `letitbe`. A dedicated `hermes` SSH user/key or MCP node auth is required.
