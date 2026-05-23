# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project posture

This repo is a working-state snapshot of a self-hosted DNS stack running on an HP t630 thin client. It serves two purposes: a portfolio artifact demonstrating self-hosted DNS competence, and a known-good rollback target.

**The live t630 is the source of truth.** Pi-hole and Unbound are running in production and serve the whole home network. This repo is not deployment automation — edits here do not affect the running system until manually deployed:

- Unbound configs: `sudo cp unbound/*.conf /etc/unbound/unbound.conf.d/ && sudo systemctl restart unbound`
- Pi-hole: `cd pihole && docker compose up -d`

## Working philosophy

Move the system toward truth, goodness, and elegance — distilled, competent, honest. Welcome changes that improve clarity, correctness, or simplicity. Reject churn.

- Risk is acceptable as long as a fallback snapshot exists in git history.
- Every commit to `main` must leave the repo in a state where `SETUP.md` would reproduce a working system on a clean Ubuntu 24.04 install.
- Use feature branches for half-finished work.

## Load-bearing known issues

The README's "Known issues and TODOs" section reflects deliberate choices or live-system realities — not a backlog to eagerly fix. Before proposing fixes to documented known issues, confirm the approach in conversation first.

| Issue | Status |
|-------|--------|
| `PIHOLE_DNS_=127.0.0.1#5335` in compose file | Came off the running container and works in production. Do not change without verifying what the live Pi-hole actually resolves through. |
| Overlapping `server:` sections across Unbound drop-in files | Messy but functional. Consolidation should be a deliberate refactor, not an incidental edit. |
| `ttl-override.conf` sets both floor and ceiling to 86400 | Real contradiction, but the live system has run on it for weeks without issue. |

## Secrets posture

`WEBPASSWORD` in `pihole/docker-compose.yml` must remain `CHANGE_ME` in the repo. Moving secrets to a gitignored `.env` file is on the TODO list but not yet implemented — do not implement it as an incidental change.

## Documentation discipline

Keep `README.md` and `SETUP.md` in sync with any config changes. Docs drift is a primary failure mode for this kind of project. If you change a config, update the docs that describe it in the same commit.

## Unbound cache persistence

Cache persistence is implemented as four load-bearing pieces: `systemd/unbound.service.d/override.conf` (load cache on start, dump on stop), `systemd/unbound-cache-dump.timer` + `systemd/unbound-cache-dump.service` (hourly independent dump), and `scripts/unbound-cache-dump` + `scripts/unbound-cache-load`. All parts are required — do not remove any one without understanding the whole mechanism.

## AMD Carrizo GPU udev rule

`udev/99-amdgpu-performance.rules` is load-bearing for headless remote desktop performance. The Carrizo APU aggressively downclocks GPU without it. Do not remove or simplify it.

## Verification commands (non-destructive)

```bash
# Validate Unbound config syntax before restarting
unbound-checkconf

# Confirm Unbound resolves with DNSSEC
dig @127.0.0.1 -p 5335 example.com +dnssec

# Validate compose file syntax
docker compose -f pihole/docker-compose.yml config

# Confirm Pi-hole container is healthy
docker ps
```
