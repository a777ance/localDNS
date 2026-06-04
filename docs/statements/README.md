# Monthly statements

Client-facing **Network Activity Statements** plus the operator-side **Alliance Member
Portfolio** — the recurring artifacts that make the stack's invisible work visible and
justify the subscription on both sides of the equation.

The model is **pest control, not lawn care**: the value is the quiet, and the statement is
the sticker on the door that proves the work happened. Designed to be emailed, printed/mailed
on paper, and **scrollable on a phone** when opened via the QR code.

> These are **mockups of the target output** — what the generator should produce. Some figures
> need a real data source first; see [Data sourcing](#data-sourcing).

---

## Open the statements

GitHub shows `.html` as source code, not a rendered page, so there are three ways to actually *open* these:

1. **Preview images** (below) render right here on GitHub — no setup, instant look.
2. **[`index.html`](index.html)** is a gallery linking to every statement. Open it locally
   (clone/download, double-click) and each card opens the live statement.
3. **GitHub Pages** publishes the gallery at a public URL so anyone can open it in a browser.
   One-time setup: **Settings → Pages → Source: "GitHub Actions"**. The
   [`pages.yml`](../../.github/workflows/pages.yml) workflow then regenerates and publishes
   `docs/statements/` on every change; the gallery lands at the site root
   (`https://<owner>.github.io/<repo>/`). Published this way the gallery is an **installable
   PWA** — *Add to Home Screen* on a phone, *Install* in Chrome/Edge on a laptop; it opens
   full-screen and works offline. The path from here to a native app is in
   [`APP-ROADMAP.md`](APP-ROADMAP.md).

---

## Two sides of the equation

| | Audience | Artifact |
| --- | --- | --- |
| **Client** | The homeowner | A per-household 1–2 page statement, one per month |
| **Operator** | The Alliance member who manages a book of homes | One portfolio statement over all their clients, plus the bundle of individual 1-pagers |

---

## Client statements — the archetypes

One template, populated per household. The **profile**, **macros**, **compare axis**,
**suggestions**, and **"Handled For You"** log all vary with the home — this is the range a
generator would produce.

### [`client/archetype-prime-time.html`](client/archetype-prime-time.html)
Streaming-dominant household. Three tailored suggestions.

![Prime-Time household statement](previews/archetype-prime-time.png)

### [`client/archetype-home-office.html`](client/archetype-home-office.html)
Work-from-home: cloud + video-conferencing macros, daytime-peaked, upload-sensitive.
Different suggestions (UPS, call-priority QoS, wired backhaul).

![Home Office statement](previews/archetype-home-office.png)

### [`client/archetype-connected-family.html`](client/archetype-connected-family.html)
18-device family. Demonstrates the **affirmation path** — when nothing needs changing, the
suggestions section becomes a "nothing to change this month, beautifully boring" note
instead of inventing upsells.

![Connected Family statement](previews/archetype-connected-family.png)

### What's on a client statement

- **Account Summary** — period-over-period + year-to-date, brokerage-statement style.
- **Handled For You This Month** — the personal touch. Work done on the client's behalf,
  written like **local patch notes** and attributed by name ("*Cloudflare pushed a security
  update; your appliance was patched the same day — Jose*"). Always framed as *your home*,
  *your appliance*, *your living-room TV* — specific, not generic IT-speak.
- **Traffic Allocation** — a donut of volume by category. Categories only, never domains.
- **Household Profile** — traffic as "macros"; the balance assigns a monthly archetype.
- **How You Compare** — a **diverging axis** against the average home. A dotted centre line is
  the average; each bar swings **left (below) or right (above)**, coloured by *sentiment* not
  direction — green when the deviation is good regardless of which way it points (lower latency
  swings left and is green; more threats blocked swings right and is green), **grey** when it's
  merely neutral (data volume, streaming share). Real units stay on every bar.
- **Have You Tried? / Our Read** — continuous-improvement suggestions, or the affirmation.
- **Connect in the Alliance** — a profile-matched member (face + blurb + connect QR). Opt-in.
- **See For Yourself** — QR codes to the live status page and the scrollable online statement.
- **Service Status** + an aggregate-only privacy note.

---

## Operator portfolio — earning the keep

### [`operator/alliance-member-portfolio.html`](operator/alliance-member-portfolio.html)
Jose manages 20 homes. Every month he gets one view of the whole book: fleet KPIs, issues
**percolated to the top** (High / Med / Watch, each owned by name with status + ETA), the
monthly work log / fleet changelog that carries the subscription, and the full roster that
indexes the bundle of 1-pagers.

![Alliance Member Portfolio](previews/alliance-member-portfolio.png)

---

## The pipeline (the generator)

Everything renders from JSON — the template never holds data. The flow:

```
 ON THE BOX (t630)                          THE BRAIN                    RENDER
 collect/collect_stats.py  ──► stats.json ──► compose.py ──► data/clients/<home>.json ──► generate_client.py ──► client/*.html
   • Pi-hole FTL (queries/blocks/devices)      • classifies the archetype                                         │
   • Uptime Kuma /metrics (uptime/latency)       from the traffic mix                                             ├─► roll up ─► generate_operator.py ─► operator/*.html
   • wg show (VPN sessions)                     • computes the compare-axis deltas
   • nftables counters (per-category bytes)     • picks chips + suggestions
                                                • merges the operator sidecar
                                                  (Handled-For-You log, Alliance match)
```

| Path | What it is |
| ---- | ---------- |
| [`data/clients/*.json`](data/clients) | One file per home = the single source of truth a statement renders from |
| [`data/portfolio.json`](data) | The operator's book (KPIs, attention queue, work log, roster) |
| [`tools/generate_client.py`](tools/generate_client.py) | Template + renderer; self-seeds the sample JSON, then renders from `data/` |
| [`tools/generate_operator.py`](tools/generate_operator.py) | The fleet roll-up renderer |
| [`tools/compose.py`](tools/compose.py) | The classifier + assembler — turns measured stats into a statement JSON |
| [`tools/collect/collect_stats.py`](tools/collect/collect_stats.py) | On-box gatherer (Pi-hole / Kuma / wg / nft). `--sample` runs anywhere |
| [`tools/collect/categories.json`](tools/collect/categories.json) | Domain → category map |
| [`tools/collect/nftables-accounting.nft`](tools/collect/nftables-accounting.nft) | The flow-accounting ruleset that yields per-category bytes |
| [`tools/collect/populate_sets.py`](tools/collect/populate_sets.py) | Resolves `categories.json` → IPs and feeds the nft sets — the piece that makes volume real. Runbook in [`collect/README.md`](tools/collect/README.md) |
| [`tools/collect/sample-sidecar.json`](tools/collect/sample-sidecar.json) | Example operator sidecar (narrative + cohort + prior/YTD) |

Regenerate the mockups (only dependency is `segno`):

```bash
cd docs/statements
python3 tools/generate_client.py      # renders client/*.html from data/clients/*.json
python3 tools/generate_operator.py    # renders operator/*.html from data/portfolio.json
```

Run the real pipeline end-to-end (works with no box via `--sample`):

```bash
python3 tools/collect/collect_stats.py --sample --out /tmp/s.json
python3 tools/compose.py --stats /tmp/s.json --sidecar tools/collect/sample-sidecar.json \
        --out data/clients/archetype-prime-time.json
python3 tools/generate_client.py
```

**Real customers render PRIVATELY.** This repo is public (GitHub Pages), so a real home's
name and figures must never be written here. The tools are generic and carry no customer
data — only the JSON does — so point the generator at a private location instead:

```bash
# stats.json comes from the box; sidecar + output live in a PRIVATE repo
python3 tools/compose.py --stats /tmp/HH-0001.stats.json --sidecar ~/customers/households/HH-0001-dave/sidecar.json \
        --out ~/customers/households/HH-0001-dave/data/2026-06.json
python3 tools/generate_client.py --data-dir ~/customers/households/HH-0001-dave/data \
        --out-dir  ~/customers/households/HH-0001-dave/statements
```

`--data-dir` skips the built-in mockups automatically, so a private dir only ever holds that
home's real statement. Keep both the JSON and the rendered HTML in the private repo.

Prose is deterministic and templated today; `compose_prose()` is the single seam to swap in a
Claude (Haiku) call for richer copy (~$0.01/home) once you want it — the inputs are already assembled.

---

## Data sourcing

Read before shipping to a paying client. Be honest about which figures are real:

| Figure | Source | Status |
| ------ | ------ | ------ |
| Queries resolved, threats blocked, protection rate, device count | Pi-hole FTL (`pihole-FTL.db`) | **Real** — available today |
| Uptime, peak latency | Uptime Kuma `/metrics` | **Real** — available today |
| VPN session count | `wg show` | **Real** — available today |
| "Handled For You" log | The operator's own change record (the sidecar) | **Real** — operator-maintained |
| **Traffic volume in GB, by category** | nftables accounting (`nftables-accounting.nft` + `populate_sets.py`) | **Built — run it on the box.** Ruleset *and* IP-set populator now both ship here; load the ruleset, schedule `populate_sets.py`, and these sections are real (runbook: [`collect/README.md`](tools/collect/README.md)). Until then the committed examples use sample volume. |
| Demographic benchmark averages | the cohort block in the sidecar | **Needs a real cohort dataset**, or it's a placeholder. Don't print invented peer averages on a kept document. |

The committed examples use **sample data** for the volume-based sections. Before these go out for
money, stand up the flow-accounting layer (or scope the statement to what Pi-hole + Uptime Kuma
already prove). QR codes are real (`segno`) and inlined as SVG — every statement is a single
self-contained file with no external assets and no JavaScript.

**The generator self-scopes — honest by construction.** `compose.py`/`generate_client.py` omit
any section they lack real data for, rather than fake it: no per-category volume → no Traffic
Allocation donut **and** no Household Profile/suggestions (both are traffic-mix–derived); no real
cohort (or a `_DO_NOT_SHIP` placeholder) → no "How You Compare"; no real Alliance match → no
Connect card. So a first statement built from only Pi-hole + Uptime Kuma + `wg` renders cleanly
as Account Summary + Handled For You + See For Yourself + Service Status. Full `cfg`s (the three
sample homes) are unaffected — they still render every section, byte-for-byte as before.
