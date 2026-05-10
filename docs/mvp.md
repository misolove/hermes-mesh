# MVP Plan

## MVP 0: Repository and design pack

Status: current.

Deliverables:

- architecture doc
- threat model
- MCP tool spec
- example node config
- skill drafts
- install/service placeholders

## MVP 1: Ubuntu Remote MCP Node

Goal:

MacBook Hermes can call an MCP tool running on Ubuntu over Tailscale and safely get system/service info.

Tools:

- `system_info()`
- `disk_usage()`
- `service_status(service)`
- `run_command(command, cwd?, timeout?)` with tiny allowlist
- `recent_logs(unit, lines)`

Implementation tasks:

1. Create Python package skeleton.
2. Add YAML config loader.
3. Add bearer auth middleware.
4. Add policy engine for commands/services.
5. Add audit JSONL writer.
6. Implement system tools.
7. Implement service status/log tools.
8. Add systemd unit.
9. Add smoke test script.
10. Register server in MacBook Hermes config.

Success criteria:

- MacBook Hermes discovers `mcp_ubuntu_mail_*` tools.
- `system_info()` returns hostname, OS, uptime.
- `service_status("nginx")` returns active/inactive without requiring raw SSH.
- Audit log records each call.

## MVP 2: Safe file and Git operations

Tools:

- `list_dir(path)`
- `read_file(path, offset?, limit?)`
- `write_file_with_backup(path, content)`
- `patch_file(path, old, new)`
- `git_status(repo)`
- `git_diff(repo)`

Success criteria:

- Access restricted to configured allow paths.
- Denied paths cannot be read.
- Writes always create backups and return diffs.
- Git status/diff works for homepage repo.

## MVP 3: Homepage deploy workflow

Tools:

- `homepage_status()`
- `homepage_diff()`
- `deploy_homepage(plan_only=true)`
- `deploy_homepage(apply=true, plan_id=...)`
- `rollback_homepage(backup_id)`
- `nginx_test()`
- `nginx_reload()`

Success criteria:

- Deployment is plan/apply, not a blind one-shot.
- Build/test commands run before reload.
- `nginx -t` passes before reload.
- Health check confirms site is reachable.

## MVP 4: Mail server diagnostics

Tools:

- `mail_services_status()`
- `mail_queue()`
- `mail_recent_errors(lines=200)`
- `mail_tls_status()`
- `mail_dns_check(domain)`
- `postfix_reload()`
- `dovecot_reload()`

Initial mode should be mostly read-only.

## MVP 5: Remote Hermes delegation

Tools:

- `remote_hermes_chat(prompt, profile?, timeout?)`
- `remote_hermes_job_start(prompt, profile?)`
- `remote_hermes_job_status(job_id)`
- `remote_hermes_job_result(job_id)`
- `remote_hermes_job_cancel(job_id)`

Default mode:

- read-only analysis
- no destructive actions
- controller Hermes reviews and applies changes through MCP tools

## Rollout checklist

- [ ] Create unprivileged `hermes` user on Ubuntu.
- [ ] Configure Tailscale MagicDNS and ACLs.
- [ ] Generate bearer token and store outside git.
- [ ] Install node service under `/opt/hermes-mesh`.
- [ ] Bind service to Tailscale IP or localhost behind Tailscale-only proxy.
- [ ] Configure systemd service.
- [ ] Add restricted sudo wrappers.
- [ ] Register MCP server in MacBook Hermes config.
- [ ] Restart Hermes and verify tool discovery.
- [ ] Run smoke tests.
- [ ] Validate audit logs.
