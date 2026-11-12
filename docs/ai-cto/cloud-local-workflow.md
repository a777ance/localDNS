# Cloud + local sessions: the working split

Status: proposed workflow, recorded from the 2026-11-12 Decide list. Not yet exercised end to end.

## The four rules

1. **Cloud builds, local deploys.** A cloud session makes the change on a branch cut from `leader`, pushes it, and opens a draft PR. A local checkout on the founder's laptop pulls it (`tools/laptop-sync.sh` fast-forwards a clean `leader` checkout) and runs the deploy-and-verify steps from `docs/DEPLOY-PROTOCOL.md` against the t630. Cloud sessions cannot reach the t630 (LAN and WireGuard only), so they never deploy.
2. **Attach a folder only when needed.** A cloud session attaches a local folder through Remote Control only when it needs live files or tools that exist only on the computer. Attaching is not the default. A cloud session never touches the live box, even when attached.
3. **Handoffs use `send_message`.** When a cloud session finishes a PR, it messages the local session to deploy it. The reverse also holds: a local session that finds a defect on the box messages a cloud session to fix it on a branch.
4. **One writer per branch.** Never run two sessions on the same files or the same branch at the same time. Each session cuts its own branch from `leader`, per `docs/ai-cto/branches.md`.

## Why

- The t630 is the source of truth and is reachable only from the LAN or WireGuard (CLAUDE.md §0, §B).
- Secrets (`.env`, vault keys) stay off the cloud container.
- Two writers on one branch produce merge conflicts and lost work.

## Still open

- Confirm that Remote Control folder attach works on the founder's account (the tool reports availability per account).
- Decide whether the handoff message carries the PR link only or also the deploy steps.
