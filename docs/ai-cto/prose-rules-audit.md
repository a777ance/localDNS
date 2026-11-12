# Prose-only rules: audit (SQ-008)

Measured 2026-11-12. For each rule in `CLAUDE.md` that lives in prose, this names the gate that
checks it, or says none does. `python3 tools/matrix.py orient.retrofit` does NOT cover house style,
provenance or the Jury values: it audits the reply and stored-state rules only. The table below is
what covers them.

| Rule | Where it is stated | Gate that checks it | Measured now |
| ---- | ------------------ | ------------------- | ------------ |
| Time-based content newest-first; alphabetical lists Z to A | CLAUDE.md, house style | none | not checked. Spot read of `session-log.md` and `decisions` is newest-first; `check-decisions.py` checks DEC order only |
| Font: Gill Sans MT stack | CLAUDE.md, house style | none | measured: `docs/statements/tools/style.css` carries the full stack 12 times; `operator-style.css` carries "Gill Sans" 8 times |
| Provenance tags and the `verify:` route | CLAUDE.md, Provenance Ladder | `tools/check-provenance.py` (in the commit gate) | gated |
| Jury sampler values match §G | CLAUDE.md §G | `tools/check-doctrine.py` (in the commit gate) | gated |
| Bifrost sweep, template and glyph roles identical | CLAUDE.md §H | `tools/check-docs.py` (in the commit gate) | gated |
| No secrets in git | CLAUDE.md, portfolio conventions | none | not checked by a gate; `.gitignore` covers `.env` only |
| Statement honesty: no unmeasured figure | CLAUDE.md, honesty of the kept document | `tools/check-statements.py` (in the commit gate) | gated, now including the rendered page (SQ-001) |
| Reply rules (state word, landing, letters, no hedges, command cd) | `docs/ai-cto/reply-style-full.md`, Stop hook | `.claude/hooks/decide-act.py` and `tools/check-stop-hook.py` | gated |

## Result

Gated: five of eight. Not gated and worth a gate or a line of honest prose:
- The Z-to-A and newest-first ordering (house style). No check reads it. It stays prose until a
  check is written, and a check is a new item, not part of this audit.
- The secrets rule has only `.gitignore` behind it. A check that scans tracked files for key-shaped
  strings would be the gate. Not written here.

The audit writes no gate. It names the two gaps so the founder can decide whether each becomes an item.
