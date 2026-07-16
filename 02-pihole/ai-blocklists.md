# AI blocklists for Pi-hole

Optional adlists that block generative-AI providers, AI-generated-content sites, and
NSFW AI chatbots — a category the base ad/tracker lists don't cover. Sourced from
[Firewalla's `fw-public-lists`](https://github.com/firewalla/fw-public-lists) and the
upstream it points at. Deploy with `build-ai-adlists.sh` (same folder).

## TL;DR

```bash
# on the t630, with the pihole container up
bash ~/pihole/build-ai-adlists.sh
```

That converts + registers all three lists and rebuilds gravity. Everything below is
the "why" and the manual path if you'd rather click through the UI.

## The catch: two of the three lists are NOT Pi-hole format

This is the whole reason there's a script instead of three adlist URLs. Do **not**
paste the Firewalla raw URLs straight into Pi-hole → Lists — two of them silently
ingest zero domains.

| Source file | Lines | Format | Pi-hole action |
| ----------- | ----- | ------ | -------------- |
| `noai_hosts.txt` (uBlock upstream) | ~2300 | `0.0.0.0 domain` hosts | **add URL directly** — native format |
| `ai-provider.txt` (Firewalla) | ~1200 | `*.domain` wildcard glob | **convert** `*.x` → `\|\|x^` first |
| `nsfw-ai.txt` (Firewalla) | ~90 | `*.domain` wildcard glob | **convert** `*.x` → `\|\|x^` first |

Firewalla's lists use its own target-list syntax: one leading-wildcard glob per line
(`*.example.com`). Pi-hole's gravity parser treats `*.example.com` as an **invalid
domain** and drops it, so a raw-URL adlist pointed at those files ingests ~0 entries
with no error. The fix is to rewrite each line to ABP syntax `||example.com^`, which
Pi-hole v6 **does** support and which blocks the apex plus every subdomain — the
intended meaning of the `*.` glob.

Firewalla's third file, `ublockorigins-huge-ai-blocklist.txt`, is a one-line redirect
(`@https://…/noai_hosts.txt`) to laylavish's upstream. We skip the redirect and add
that upstream — already `0.0.0.0 domain` hosts format — as a normal remote adlist.

## What the script does

1. Downloads `nsfw-ai.txt` and `ai-provider.txt`, converts each `*.domain` → `||domain^`,
   and copies the result into the running pihole container at
   `/etc/pihole/ai-lists/*.abp` (that path is the persistent `pihole_data` volume, so
   the files survive restarts — no compose change or new bind mount needed).
2. Registers three adlists in `gravity.db` with `INSERT OR IGNORE` (the `address`
   column is `UNIQUE`, so re-runs never duplicate): the two `file://…` local lists
   plus the remote uBlock URL.
3. Runs `pihole -g` to rebuild gravity.

It's idempotent and cron-safe. Weekly is plenty (these lists gain entries over time):

```cron
0 4 * * 1  /usr/bin/bash /home/USER/pihole/build-ai-adlists.sh >/dev/null 2>&1
```

## Manual path (Pi-hole web UI, no script)

Only the uBlock list works this way; the two Firewalla lists still need conversion.

1. **Settings → Lists → Add a new list**, address:
   `https://raw.githubusercontent.com/laylavish/uBlockOrigin-HUGE-AI-Blocklist/main/noai_hosts.txt`
2. For the Firewalla two, convert locally and host the output somewhere Pi-hole can
   read (a `file://` path inside the container, or any URL). The conversion is just:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/firewalla/fw-public-lists/master/ai-provider.txt \
     | awk '/^[[:space:]]*#/||/^[[:space:]]*$/{next}{gsub(/\r/,"");sub(/^\*\./,"");print "||" $0 "^"}'
   ```
3. **Tools → Update Gravity** (or `pihole -g`).

## Verify

```bash
# the three AI adlists are registered and enabled
docker exec pihole pihole-FTL sqlite3 /etc/pihole/gravity.db \
  "SELECT id, enabled, address FROM adlist WHERE comment LIKE 'AI:%';"

# a known AI-provider domain now resolves to the block answer (0.0.0.0 / NXDOMAIN)
dig @127.0.0.1 perplexity.ai +short
```

## Licenses / provenance

- `fw-public-lists` — GPL-2.0 (Firewalla). `ai-provider.txt` upstream license listed as
  "Unknown"; `nsfw-ai.txt` authored by Firewalla.
- `noai_hosts.txt` — laylavish's uBlockOrigin-HUGE-AI-Blocklist (its own repo license).

We don't vendor these domain lists into this repo — the script fetches them at deploy
time, so the repo stays lean and the lists stay current.
