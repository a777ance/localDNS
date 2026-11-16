# Handover kit: taking this repo to another Claude account

Everything a second account needs to stand the system up from GitHub alone and prove it works. Written
2026-11-16, when `leader` was at `7c21e0b` and the acceptance series had just been run on the founder's account.

provenance: M · the series and every figure cited were measured on the founder's account · 2026-11-16 · verify: `docs/ai-cto/rsi/runs/acceptance-2026-11-16.json`

## Before you start

- The new account can read <https://github.com/a777ance/localDNS> (branch `leader`).
- The session there has the artifact tools (publish, declare capabilities, database read and write) and a shell.
- Nothing is carried by hand. The artifact, its link and its mailbox do not cross: the new account publishes its
  own. `ARTIFACT.md`, "Moving the whole thing to another Claude account", lists what crosses and what does not.

## The prompt

Paste this as the first message of a session on the new account:

```text
Clone https://github.com/a777ance/localDNS at branch leader and read
CLAUDE.md, then docs/ai-cto/handoff.md and docs/ai-cto/planned.md.

Your task is in tools/browser/explorer/HANDOVER.md and
tools/browser/explorer/ARTIFACT.md, section "Moving the whole thing to
another Claude account". Do its three steps: rebuild and publish the
explorer as a new artifact on this account, commit the new slug and dist
on a branch of your own (do not push to leader), then run the four-shot
acceptance series and grade it.

Before the series, re-measure the platform's limits as
docs/ai-cto/rsi/runs/exp-width.json describes: they were measured on
another account and may differ here.

Report each shot against its mark, with the hash comparison, and read
any miss before quoting a score. Say plainly what failed.
```

## What the session will do, and what the person does

| Step | Who | What |
| --- | --- | --- |
| 1 | session | `bash tools/browser/explorer/rebuild.sh OUT_DIR`: rebuilds the four served files and checks them against `dist/SHA256SUMS` |
| 2 | session | publishes them as a new artifact, declares `sample`, `db` and `downloads`, replaces the slug in the three files `ARTIFACT.md` names |
| 3 | person | opens the new artifact once and grants Claude access when it asks |
| 4 | session | writes the width probe (`runs/exp-width.json`) to the mailbox |
| 5 | person | reloads the page and keeps it on screen until its chat shows a result; a phone pauses a page that leaves the screen |
| 6 | session | writes the four acceptance shots; the person reloads and waits about two minutes |
| 7 | session | reads the results, compares each `check.expected_sha256` with its own, reads the misses, reports |

## The marks

The four shots and their pass marks are in `ARTIFACT.md`. On the founder's account on 2026-11-16: 4 of 4 mail
asks, 178 of 178 titles, 109 of 110 ids by screening, 50 of 54 ids by full-text sweep.

## What was measured here and must be re-measured there

| Fact | Here | Record |
| --- | --- | --- |
| model calls running at once, per open view | 2, with 4 more held and a 7th refused | `docs/ai-cto/rsi/runs/exp-width.json` |
| frames inside the page | get no model calls | `docs/ai-cto/rsi/runs/exp-frames.json` |
| a limit on use over time | exists; no number yet | `docs/ai-cto/rsi/runs/pass-10.json`, L-163 |
| the model behind `modelTier: "quick"` and a named `claude-haiku-5-5` | accepted by name | `docs/ai-cto/rsi/runs/pass-6.json` |

## Known open, none blocking

- Whether a second open view adds lanes: designed, not run (`docs/ai-cto/planned.md`, PLAN-001).
- The reply tool's refusal to answer a shot has no test of its own (L-165).
- `tools/check-statements.py` needs the `segno` module; where it is missing the check fails and nothing else does.
- The queue of leans stands at 56 open (`docs/ai-cto/rsi/QUEUE.md`); the ledger of the ten passes is
  `docs/ai-cto/rsi/LEDGER.md`.

## Reporting back

The new account's findings belong on its own branch: the new slug, a fresh `dist/`, an acceptance record beside
this one, and the re-measured limits. A pull request into `leader` is how they come home (DEC-015).
