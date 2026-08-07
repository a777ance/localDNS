<!-- provenance: O · audited against the working tree on 2026-08-07 (greps + hook exercised both ways); the framing was supplied by the founder · 2026-08-07 -->

# Warrant sites — where an invariant has to live to bind anything

**Epistemics**, here, names a run's operative **warrant configuration** — not the theory of
knowledge (that is epistemology) but the working settings a particular run executes under:

1. **Given-set** — what the run treats as established without verification. *The command
   file occupies premise position by construction; its contents enter at that rank.*
2. **Check obligation** — which claim types require a verification step before emission.
   *Where the file states none, none attaches.*
3. **Confidence policy** — what closes, and what gets named as unknown. *Silence resolves
   this to closed*, because surface confidence is uniform and generation supplies no
   downward pressure on it.

All three transfer together, and they transfer from whatever is in premise position.

**The rule this yields:** an invariant needs a **site**, not an author. Warrant transfers;
grounds stay behind.

Adopted 2026-08-07, out of the root-cause finding behind the jury honesty flags
(`04-user-services/ai-orchestration/examples/workout-bootstrap-paradox-session.md`).

---

## Why briefing prose binds nothing

CLAUDE.md is read **once, by the operator, at read time**. It is outside the read path of
any subsequent run. So an invariant that lives only there assigns nothing to any run's
given-set: two authorities are in play, and they diverge.

| Authority | Reads | Consequence |
| --------- | ----- | ----------- |
| **Operator fidelity** | the briefing | The operator follows §G faithfully — and still launches runs whose given-set omits it |
| **Run fidelity** | the command file | The run follows its file faithfully — and that file is the whole of what it was given |

The gap between them is not operator error. It regenerates on schedule, and it is what
produced the jury flags twice.

**A citation is not a site.** `.claude/commands/cardio.md` referenced CLAUDE.md §G **five
times** while its own text defined the `confidence read: unanimous / strong majority /
split` scale that §G forbids — and the file's text won, in both recorded runs. A pointer in
premise position transfers **the pointer**. Where the file's own text contradicts the cited
invariant, the text is what executes.

**Silence is an assignment, not a gap.** Because component 3 defaults to closed, a command
file that says nothing about confidence has *assigned* "report it closed". This is why the
repair to the jury commands was not "add a caveat" but "make the unknown state mandatory
and name it".

---

## The site ladder

Where an invariant can live, strongest first. Migration upward is the repair.

| Rank | Site | Binds because | Example here |
| ---- | ---- | ------------- | ------------ |
| 1 | **Mechanical check at the emission boundary** (hook, generator, CI) | The invariant decides without a reader | `.claude/hooks/gate.sh` blocks a commit failing `check-docs.py`, `check-provenance.py` or `check-doctrine.py`; `docs/statements/tools/generate_client.py` gates each optional section on `cfg.get(...)`, so "How You Compare" **cannot** render without data |
| 2 | **Fail-closed structure** | The wrong state cannot start | `${LITELLM_MASTER_KEY:?…}` in both compose files — no unsealed secret, no container |
| 3 | **Inlined text in the file that executes** (`.claude/commands/*.md`, `.claude/agents/*.md`, a script) | It is in premise position for that run | The menu prohibition and the mandatory bound line, written out in `cardio.md` / `workout.md` / `juror.md` |
| 4 | **A citation to the briefing** | Nothing. Transfers the citation | The five §G references that lost to their own file's text |
| 5 | **Briefing prose alone** | Nothing, for runs | Any invariant stated only in CLAUDE.md |

Ranks 4 and 5 are not *wrong* — they are how a human operator learns the system. They are
simply not sites, and an invariant with no rank 1–3 residence should be recorded as
unsited rather than assumed to hold.

---

## The audit

State of the working tree, 2026-08-07. "Site" means rank 1–3 above.

| Invariant | Stated in | Site | Status |
| --------- | --------- | ---- | ------ |
| Statement prints only measured figures | Portfolio conventions | `generate_client.py` conditional sections | ✅ **Sited** — the section is structurally unrenderable without data |
| No secrets in git | Portfolio conventions | `${VAR:?}` in both composes · `.gitignore` · `.env.example` | ✅ **Sited** — fail-closed |
| Docs links + repo paths resolve | § 4 | `tools/check-docs.py`, now gated at commit | ✅ **Sited** |
| §G's sampler values match the code that sends them | § G | `tools/check-doctrine.py`, now gated at commit | ✅ **Sited** — landed independently on `main` the same day, same finding |
| Provenance tags are valid and R-tier never reaches the box undiffed | § 3 · `docs/provenance.html` | `tools/check-provenance.py`, now gated at commit | ✅ **Sited** (2026-08-07) |
| Never supply jurors an answer menu | § G | inlined in `cardio.md` / `workout.md` / `juror.md` | ✅ **Sited** (2026-08-07) |
| A keyless plurality is unpriced — name the unknown | § G | inlined mandatory bound line | ✅ **Sited** (2026-08-07) |
| Measure `p`, don't guess it | § G | cited by the jury commands; `calibrate` exists but nothing requires it | ⚠️ **Cited only** — decides mechanically only when a labelled set exists |
| RCPS — root-cause and record, interleaved | § 3 | none | ❌ **Unsited** — operator practice |
| Never add sensitive domains to the forward path | § B | none | ❌ **Unsited** — *and mechanically checkable*: a checker could diff `streaming-forward.conf`'s zone list against a sensitivity denylist. Highest-value open repair |
| Box is the source of truth — diff before overwrite | § 3 · DEPLOY-PROTOCOL | none | ❌ **Unsited** — needs SSH; the commit gate cannot see the box |
| House style: newest-first, Gill Sans everywhere | House style | none | ❌ **Unsited** — partly checkable (the font stack is a grep; all `docs/*.html` currently comply by discipline alone) |

---

## Consequences for how a run reports

Component 3 has a vocabulary already, and it is not a metaphor. **Evidentiality** is the
grammatical marking of how a speaker came to hold a claim — witnessed, inferred, reported —
and several languages mark it *obligatorily* on every finite verb. A generator with no
evidential marking emits every assertion in **one mood**, and the command file is where
that mood's defaults are set. The Provenance Ladder (`docs/provenance.html`) is the
artifact-level evidential system; this file is the run-level one. They are the same
mechanism at two scales, which is why the tiers do duty as marks:

> `[measured]` a figure this run produced · `[observed]` read off the source of truth ·
> `[derived]` follows from stated inputs · `[reconstructed]` rebuilt from a description ·
> `[asserted]` intent or plan · `[unknown]` — **the mark silence would have suppressed.**

---

## Revision log

| Date | Change |
| ---- | ------ |
| 2026-08-07 | File created. Warrant configuration defined (given-set · check obligation · confidence policy); the site ladder; the working-tree audit; `.claude/hooks/gate.sh` added as a rank-1 site for all three static checks, exercised in both directions before landing. Merged with `main`'s independent §G clause→site audit (`tools/check-doctrine.py`), which reached the same finding from the sampler side the same day. |
