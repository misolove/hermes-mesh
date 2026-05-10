# MCP Tool Specification

## Naming

Hermes registers MCP tools as:

```text
mcp_{server_name}_{tool_name}
```

For the first Ubuntu node, expected names are similar to:

```text
mcp_ubuntu_mail_system_info
mcp_ubuntu_mail_service_status
mcp_ubuntu_mail_git_status
```

## Common result shape

```json
{
  "ok": true,
  "node_id": "ubuntu-mail",
  "tool": "system_info",
  "data": {},
  "warnings": [],
  "audit_id": "20260510T153000Z-abc123"
}
```

Error shape:

```json
{
  "ok": false,
  "error": {
    "code": "policy_denied",
    "message": "Path is outside allowed roots"
  },
  "audit_id": "20260510T153000Z-def456"
}
```

## System tools

### `system_info()`

Returns hostname, OS, kernel, uptime, current user, node id, Tailscale IP if available.

### `disk_usage(paths?)`

Returns `df -h`-style disk usage for configured paths.

### `memory_usage()`

Returns memory and swap usage.

### `port_list()`

Returns listening ports, preferably via `ss -ltnup` with sensitive process args redacted.

## Command tool

### `run_command(command, cwd?, timeout?)`

Policy:

- command must match allowlist
- deny patterns always win
- cwd must be under allowed paths if provided
- timeout has a strict upper bound
- output length is capped
- command and result are audited

This should be used sparingly. Prefer typed tools for common workflows.

## File tools

### `list_dir(path)`

Allowed only under configured path allowlist.

### `read_file(path, offset?, limit?)`

Must deny private keys, shadow files, TLS private keys, and other sensitive paths.

### `write_file_with_backup(path, content)`

Required behavior:

1. verify path policy
2. create timestamped backup if file exists
3. write temp file
4. optionally validate by file type
5. atomic replace
6. return unified diff
7. audit

### `patch_file(path, old, new)`

Same policy as write. Should fail unless `old` is unique.

## Git tools

### `git_status(repo)`

Runs `git status --short` and returns branch plus dirty state.

### `git_diff(repo)`

Returns capped diff for review.

### `git_pull_ff_only(repo)`

Runs `git pull --ff-only`, only for allowlisted repos.

## Service tools

### `service_status(service)`

Allowed services only.

### `service_reload(service)`

Allowed reload services only. Prefer wrapper scripts or narrowly scoped sudoers.

### `recent_logs(unit, lines=200)`

Allowed units only. Output capped and secrets redacted.

## Web tools

### `nginx_test()`

Runs `nginx -t` through configured wrapper if needed.

### `nginx_reload()`

Reloads nginx only after config test passes.

### `homepage_status()`

Returns repo status, service status, local health check, and recent errors.

### `deploy_homepage(plan_only=true)`

Returns planned commands and risk level without executing.

### `deploy_homepage(apply=true, plan_id)`

Executes a previously generated plan.

## Mail tools

### `mail_services_status()`

Checks postfix/dovecot/fail2ban status.

### `mail_queue()`

Returns queue size and sampled queue entries.

### `mail_recent_errors(lines=200)`

Summarizes recent postfix/dovecot errors.

### `mail_tls_status()`

Checks certbot certificates and expiry dates.

### `mail_dns_check(domain)`

Checks SPF, DKIM hints, DMARC, MX records. This may use public DNS queries.

## Remote Hermes tools

### `remote_hermes_chat(prompt, profile?, timeout?)`

Invokes remote Hermes for read-only local analysis by default.

### `remote_hermes_job_start(prompt, profile?)`

Starts a long-running remote Hermes task, likely via tmux/systemd-run/background process.

### `remote_hermes_job_status(job_id)`

Returns running/completed/failed state and recent logs.

### `remote_hermes_job_result(job_id)`

Returns final result.

### `remote_hermes_job_cancel(job_id)`

Cancels a remote job.
