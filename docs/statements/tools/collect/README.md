# `collect/` — the on-box data layer

This is where a statement's **measured** figures come from. Everything here runs on
the t630; nothing here writes narrative copy (that's `compose.py` + the operator
sidecar).

```
collect_stats.py  ──►  stats.json  ──►  ../compose.py  ──►  ../data/clients/<home>.json
   ▲  ▲  ▲  ▲
   │  │  │  └─ nftables counters ......... per-category VOLUME   (this dir sets up)
   │  │  └──── wg show ................... VPN sessions          (real today)
   │  └─────── Uptime Kuma /metrics ...... uptime, peak latency  (real today)
   └────────── Pi-hole FTL (sqlite) ...... queries/blocks/devices(real today)
```

Three of the four sources work the moment the box is up. The fourth — **volume by
category**, which feeds the Traffic Allocation donut and the Household Profile
"macros" — needs the flow-accounting layer in this folder stood up first. Until
then those sections render from sample data. Be honest about that with clients.

---

## Files

| File | What it is |
| ---- | ---------- |
| `collect_stats.py` | Gathers one home's measured figures. `--sample` runs anywhere. |
| `categories.json` | Domain → category map. The buckets must match the statement template. |
| `nftables-accounting.nft` | The counting ruleset: one IP-set + one byte-counter per category, hooked on `forward`. |
| `populate_sets.py` | Resolves `categories.json` domains → IPs and feeds the sets. **The piece that makes volume real.** |
| `sample-sidecar.json` | Example operator sidecar (the facts the box can't measure). |

---

## Standing up the volume layer (the only part that needs building)

The counters exist but start at zero because the IP-sets are empty. Two steps fix
that — load the ruleset, then keep the sets fed.

**1. Load the accounting ruleset** (idempotent; re-run anytime):

```bash
sudo nft -f nftables-accounting.nft
sudo nft list table inet a777acct          # sets + counters now exist, all zero
```

**2. Populate the sets from `categories.json`.** Dry-run first (resolves real DNS,
touches nothing — works on any machine):

```bash
python3 populate_sets.py | head            # prints the `add element …` script
sudo python3 populate_sets.py --apply       # on the box: actually programs the sets
```

Elements carry a `timeout` (default 24h), so CDN IPs that rotate away age out on
their own. That means the populator must run **on a schedule**, not once.

**3. Cron** (resolve a few times a day; collect monthly):

```cron
# refresh category IP-sets every 6h (CDN IPs rotate; set elements time out in 24h)
3 */6 * * *  /usr/bin/python3 /home/USER/a777ance/collect/populate_sets.py --apply >/dev/null 2>&1

# collect the running month's measured stats nightly
30 0 * * *   /usr/bin/python3 /home/USER/a777ance/collect/collect_stats.py \
             --out /var/lib/a777ance/$(date +\%Y-\%m).stats.json
```

**4. Read the counters** (what `collect_stats.py` does internally):

```bash
sudo nft -j list counters table inet a777acct
```

---

## Notes & limits

- **IPv4 only.** The sets are `ipv4_addr`. Adding AAAA would need parallel `ip6`
  sets + rules — out of scope until there's a reason.
- **Category accuracy is approximate.** A domain can sit behind a shared CDN, so a
  byte can land in the "wrong" bucket. This is fine for a *macros* view (balance,
  not precision) and is exactly why the statement reports categories, never domains.
- **Privacy holds.** Only per-category byte totals are kept — no per-domain logging,
  nothing leaves the box. That's the promise printed on every statement; this layer
  must not break it.
- **One home today.** This measures the home the box serves. The multi-home operator
  portfolio only becomes real with more than one real home behind it — see
  `../../APP-ROADMAP.md`.
