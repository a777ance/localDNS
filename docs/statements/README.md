# Monthly statements

Client-facing **Network Activity Statements** — the recurring artifact that makes
the stack's invisible work visible. One per client, per month, designed to be both
emailed and printed/mailed on paper. The model is pest control, not lawn care: the
value is the quiet, and the statement is the sticker on the door that proves the
technician was here.

Open any `.html` file in a browser; **Print → Save as PDF** for the mailed copy.
Each file is fully self-contained (inline CSS + inline SVG QR codes, no assets, no JS).

## Files

| File | What it is |
| ---- | ---------- |
| [`2026-05-david-allum.html`](2026-05-david-allum.html) | Worked example — Account A77-001, May 2026 |

## What's on the statement

- **Account Summary** — period-over-period columns + year-to-date, in the vein of a
  brokerage statement (queries, threats blocked, protection rate, uptime, latency, VPN).
- **Traffic Allocation** — a donut of volume by category. Categories only — never domains.
- **Household Profile** — the diet-app idea: traffic categories read as "macros," and the
  balance assigns a monthly archetype ("The Prime-Time Household"). Shareable, gives the
  client a reason to read.
- **How You Compare** — benchmark against similar households (demographic cohort).
- **See For Yourself** — two scannable QR codes: live status page + the online statement.
- **Service Status** + a privacy note (aggregate-only; nothing leaves the box).

## Data sourcing — read before shipping to a paying client

Not every figure here is measurable with the current stack. Be honest about which is which:

| Figure | Source | Status |
| ------ | ------ | ------ |
| Queries resolved, threats blocked, protection rate | Pi-hole FTL (`/etc/pihole/pihole-FTL.db`, or the FTL API) | **Real** — directly available |
| Uptime, latency, VPN session count | Uptime Kuma API + `wg show` | **Real** — directly available |
| **Traffic volume in GB, by category** | — | **Not measured today.** Pi-hole logs DNS *lookups*, not *bytes*. The donut/allocation/profile/benchmark need a flow-accounting layer (e.g. nftables byte counters, `ntopng`, or `nfdump`) plus a domain→category map. |
| Demographic benchmark averages | — | **Needs a real cohort dataset** or it's fabricated. Don't print invented peer averages on a document a client keeps. |

The example uses **sample data** for the volume-based sections. Before this goes out for
money, either (a) add flow accounting to the appliance, or (b) scope the statement to what
Pi-hole + Uptime Kuma can actually prove.

## Generator (planned)

The repeatable pipeline, ~$0.01/client/month:

```
Pi-hole FTL + Uptime Kuma + wg  →  stats.json
stats.json + template           →  Claude (Haiku) writes the profile + narrative copy
                                →  rendered HTML  →  Print-to-PDF  →  email / Lob.com mail
```

QR codes are generated with `segno` (pure Python) and inlined as SVG so each statement
stays a single self-contained file.
