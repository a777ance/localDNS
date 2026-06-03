# From mockup to app — the honest roadmap

> The question was "how do we get this into an app store?" The honest answer is that
> the app store is the *last* step, not the first — and most of the work between here
> and there is backend, not app. This is the real path, in order, with what's true at
> each stage. Nothing fabricated ships as real at any phase.

---

## Where we are

The statements are a **working generator** (`collect → compose → generate`). Three of
the four data sources are real today (Pi-hole, Uptime Kuma, WireGuard); the fourth
(volume by category) needs the nftables layer stood up. The multi-home "Alliance"
portfolio is **sample data** — there is one real home behind this today.

So "an app" has to answer: an app *of what data, for whom*? That defines the phases.

---

## Phase 0 — A phone/laptop demo, today ✅ (done)

The gallery is now an installable **PWA**: `manifest.webmanifest` + `sw.js` + icons,
wired into `index.html`. Published via the existing Pages workflow it:

- opens at a real URL on **any laptop or phone** browser;
- **installs** to the home screen / dock (Add to Home Screen on iOS, Install on
  Chrome/Edge desktop + Android) with the A777ance icon, no app store;
- works **offline** once opened (handy for demoing with no signal).

This is not throwaway: the PWA *is* the UI a native wrapper reuses verbatim in Phase 4.

**To publish:** repo **Settings → Pages → Source: "GitHub Actions"** (one-time), then
the `pages.yml` workflow deploys `docs/statements/` to
`https://<owner>.github.io/<repo>/`.

---

## Phase 1 — Make one home's numbers real

Close the one measured-data gap so the demo shows *this* home, not samples.

- Stand up the volume layer: `collect/nftables-accounting.nft` + `collect/populate_sets.py`
  (see `collect/README.md`).
- Run `collect_stats.py` → `compose.py` → `generate_client.py` on the box on a schedule.
- **Gate:** only figures that are measured get printed as real. Peer benchmarks stay
  labeled illustrative until there is a real cohort dataset.

---

## Phase 2 — The service backend (the real prerequisite for an app)

The QR codes already promise things that **don't exist yet**:

| QR target | Promises | Needs |
| --------- | -------- | ----- |
| `status.a777ance.com/<home>` | live per-home status page | a hosted status view + per-account scoping |
| `my.a777ance.com/<acct>` | password-protected online statement | **auth** + an API serving each account's statement JSON + history |
| `alliance.a777ance.com/connect/<id>` | opt-in member directory | a directory service (only if/when the Alliance is real) |

This is the actual "backend." An app is just a client to it. Minimum viable:

1. A host — the t630 can serve it behind the existing tunnel, or a small VPS.
2. Auth — one login per account; statements scoped to the logged-in home.
3. An API — `GET /statement/<period>` returns the JSON the generator already
   produces; `GET /status` returns live Uptime-Kuma-backed health.
4. TLS + the real domains.

No "Claude" piece is required here — it's a standard small web stack. (Claude Haiku
for richer statement prose, `compose_prose()`, stays an optional, default-off add-on.)

---

## Phase 3 — Multi-home / operator reality

The operator portfolio (`generate_operator.py`) becomes a real document only when
there is **more than one real home** under management. Today its 20-home book is
`random.seed(77)` sample data and must stay labeled as such. When real homes exist,
add a roll-up step (per-home JSON → `portfolio.json`); until then, don't manufacture
a fleet.

---

## Phase 4 — Native app + the stores

Only now does "app store" enter. The PWA from Phase 0 wraps directly:

- **Wrapper:** Capacitor (or similar) loads the web UI into iOS/Android shells —
  reuses ~100% of what's built. Add native bits only if needed (push, biometrics).
- **Apple App Store:** Apple Developer Program ($99/yr; identity verification can
  take a day+), App Store Connect setup, privacy labels, then **App Review** — count
  on days and at least one rejection round, not same-day.
- **Google Play:** $25 one-time. New **personal** developer accounts must run a
  closed test with ~20 testers for ~14 days before production access (org accounts
  differ). So Play isn't same-day for a fresh personal account either.

**Realistic timeline:** ~2–6 weeks from "Phase 2 backend done" to a live listing —
dominated by backend + review, not by the app shell.

---

## The honesty gate (every phase)

The repo's own rule: *"nothing here is aspirational"* (SKILLS.md), *"don't print
invented peer averages on a kept document"* (statements README). A document that
goes out as real — on paper, in an inbox, or in an app — only shows figures we can
stand behind. Samples are fine; samples labeled as real are not. This is also what
keeps a public app-store submission out of "misleading content" rejection territory.
