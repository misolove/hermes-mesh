# Threat Model

## Security goal

Hermes Mesh should let an AI agent operate remote machines without granting unrestricted root access or public internet exposure.

## Assets

- SSH keys
- API/model provider keys
- website source and deployment credentials
- mailboxes and mail server configs
- TLS private keys
- DNS credentials
- user home directories
- audit logs
- Tailscale network access

## Trust boundaries

```text
LLM output is untrusted.
MCP node is trusted only to enforce policy.
Tailscale network is private transport, not a complete authorization model.
Bearer token authenticates the controller to the node.
Sudo wrappers are the privileged boundary.
```

## Main risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Unrestricted shell tool | full server compromise | command allowlist, deny patterns, no root process |
| MCP endpoint exposed publicly | remote takeover | bind to Tailscale IP only, firewall, token auth |
| Token leak | remote tool access | env/secret file, redacted logs, rotation |
| Prompt injection from logs/files | unsafe action | approval gates for writes/destructive actions |
| Bad file write | service outage | backups, temp write, validation, rollback |
| Bad nginx/postfix config | website/mail outage | `nginx -t`, `postfix check`, reload only after validation |
| Sudo overgrant | root compromise | wrapper scripts only, no `sudo ALL` |
| Remote Hermes autonomy | unsupervised mutation | default read-only, controller approval |
| Audit log leaks secrets | credential exposure | hash/redact sensitive args |

## Minimum security requirements

1. Bind node server only to Tailscale IP or localhost behind Tailscale proxy.
2. Require Bearer token for every call.
3. Store token outside git.
4. Run node as unprivileged user.
5. Use command allowlist and path allowlist.
6. Use denylist for private keys, TLS private dirs, shadow files, root home.
7. Every write must create a timestamped backup.
8. Every remote action must append to JSONL audit log.
9. Sudo must be limited to wrapper scripts or very narrow service commands.
10. Destructive actions require explicit user approval and should not be one-step tools.

## Recommended approval policy

| Action | Default |
| --- | --- |
| read status/logs/files in allowed paths | allowed |
| git status/diff | allowed |
| build/test | allowed |
| reload nginx/postfix/dovecot | allowed with policy |
| write website content | allowed only with backup + diff |
| edit service config | plan then approval |
| restart services | approval |
| package install/upgrade | approval |
| firewall/DNS changes | approval |
| delete users/mailboxes/data | approval, usually manual |
| reboot | approval |

## Explicit non-negotiables

- Never commit real bearer tokens.
- Never run the MCP node as root.
- Never expose unrestricted `run_command`.
- Never allow `rm -rf`, disk formatting, user deletion, or raw firewall mutation through generic tools.
- Never grant `hermes ALL=(root) NOPASSWD: ALL`.
