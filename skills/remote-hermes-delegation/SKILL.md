---
name: remote-hermes-delegation
description: Delegate read-only or bounded jobs from one Hermes instance to another remote Hermes instance.
version: 0.1.0
author: Lerippi + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, delegation, remote-agent, tailscale, jobs]
---

# Remote Hermes Delegation

## Use when

A remote machine has Hermes installed and local context/tools that make it a better worker for a task.

## Principle

The controller Hermes delegates analysis or bounded execution. The remote Hermes should not bypass the controller's approval policy.

## Default mode

- read-only analysis
- no destructive actions
- no direct secret printing
- bounded runtime
- final result returned to controller

## Job types

- `remote_hermes_chat`: one-shot analysis
- `remote_hermes_job_start`: long-running job
- `remote_hermes_job_status`: poll job
- `remote_hermes_job_result`: fetch result
- `remote_hermes_job_cancel`: cancel job

## Verification

Controller must verify remote claims when possible:

- read back changed files
- check git diff
- run service status
- run health checks
- inspect audit logs

## Approval gates

Remote Hermes may propose changes. Controller asks the user before high-risk application.
