# The explorer artifact: where it lives and how it is rebuilt

The repo explorer runs as a claude.ai artifact owned by the founder, private to him.

| | |
| --- | --- |
| Title | localDNS (leader): repo explorer with Claude |
| Slug | `0cbd6a53-69fa-4050-bfc8-d1cabb176e86` |
| Link | <https://claude.ai/artifact/2aFAqChU6xYTiwEc1ukh8R> (opens only for its owner) |
| Shared with | owner only (`read: owner`) |
| Runtime contract | 0.2.96 |
| Capabilities | `{"sample": {}, "db": {}, "downloads": true}`: Claude calls from the page, one shared document store, and saving a file (the mailbox export) |

provenance: O · read with the artifact tools (`read_declaration`, `list_files`) after the last publish · 2026-11-15 · verify: same calls

## What it serves

`build.py` writes all four files from a checkout. The build is deterministic in any clone, shallow or full.
`dist/SHA256SUMS` names the live version, the commit it was built from, and the hash of every file; `dist/` is
left out of the page's own snapshot, so the page shows `leader` exactly as it was at that commit.

| File | What it is |
| --- | --- |
| `index.html` | the page: file browser, chat, the JS hook ports, trace, Mail, the shot engine |
| `repo.json` | every tracked text file but `dist/`, with branch, commit and CLAUDE.md's content hash |
| `heads.json` | the first 800 characters of each text file, so a mail turn starts before repo.json loads |
| `bin.json` | images, base64, loaded only when one is opened |

The full round trip, workbench to git and back, is `GATE.md`; step 4 is `restate.sh`. Keeping the page in step with `leader`: after any commit outside `dist/`, rebuild with `EXPLORER_BRANCH=leader`,
publish, and commit the new `dist/` alone. Then `leader` and the page differ only in `dist/`, which is the record
of the page itself.

## What runs inside it

- **The Claude in the page** answers questions with three tools over the snapshot (`list_files`, `read_file`,
  `search`) and four mail tools. It is not Claude Code: it cannot run a shell, write files, commit or push.
- **The harness.** The repo's own hooks from `.claude/settings.json` run as JavaScript ports
  (`tools/browser/hooks.js`, tested for identical output against the Python and shell originals): SessionStart
  (`refeed.sh`), PreToolUse (`cardinal.py`, `gate.sh`), PostToolUse (`timing.py`), Stop (`momentum.sh`,
  `decide-act.py`). A reply the Stop hook blocks is revised once, as in Claude Code. One rule differs, and the page
  says so to the model: it cannot start sub-OODA loops, so open items go on a "For a Claude Code session:" line.
- **Debug and Full trace.** Every turn, model call, tool call and hook run is a span, with the files each hook read
  and wrote; Full trace exports them as JSON.
- **The mailbox and the shot engine.** The `mail` collection of the artifact's database, shared by the founder,
  the page and Claude sessions. Opening the page fires every waiting shot from a session: see
  `tools/telepathy/ARTIFACT-BUS.md`. The Mail panel's "Export mailbox (JSON)" saves the whole collection.

## The built page, committed

`dist/` holds what the artifact serves, as files a person or a fresh Claude can open without building anything:
`index.html` (the whole front end: the page, the JavaScript hook ports and the shot engine, in one file) and
`heads.json`. `dist/SHA256SUMS` lists all four served files and the commit they were built from. `repo.json`
and `bin.json` are not committed: they are this repo's own files repacked (2 MB and 5 MB), and
`rebuild.sh` regenerates them from that commit and proves all four byte for byte:

    bash tools/browser/explorer/rebuild.sh OUT_DIR

The back end is the platform: the artifact's `sample`, `db` and `downloads` capabilities, declared in `artifact.json`. The
database holds only the mailbox (`tools/telepathy/ARTIFACT-BUS.md`); there is no other server.

## Reconstruct in a fresh Claude profile

The slug belongs to the founder's account; a new profile gets a new one. From a session with the artifact tools:

1. `bash tools/browser/explorer/rebuild.sh OUT_DIR` (or build the current tree with `build.py`).
2. `publish_files` with the four files from `OUT_DIR` and no slug: this creates the artifact. Title and icon are
   in `artifact.json`.
3. `declare_capabilities` with `artifact.json`'s `capabilities`.
4. Replace the slug in `.claude/skills/telepathy-mail/SKILL.md` and `tools/telepathy/ARTIFACT-BUS.md`, and in
   `artifact.json`.
5. Open the page once and grant Claude access when it asks. The mailbox starts empty; to carry old mail over, write
   an export's documents back with `db_write`.

## Republish after a change

From a session with the artifact tools (claude.ai cloud, Cowork):

1. Build: `python3 tools/browser/explorer/build.py OUT_DIR`.
2. Read the live version: `get_artifact` with the slug above.
3. Publish: `publish_files` with the four files from `OUT_DIR`, `base_version` from step 2.
4. If a capability is added or removed, `declare_capabilities` (declare before publishing code that uses a new one;
   publish first when dropping one).
5. Run the page tests (`tools/browser/README.md`) before step 3.

## The mailbox on 2026-11-15

The database is live data, not repo content, and it is not copied here. What it held when this was written, all
from this session's tests: the first messages both ways (03:55 to 04:01 UTC); a four-round ping pong (10:31 to
10:40); the 30-round runs 1 to 3, sent one message per round (10:54 to 11:17); runs 4 and 5, 30 questions in one
message each (11:22, 11:34); run 6, the first shot with a nested question and a chain (11:45). The questions sent
are in `tools/browser/test/data/`, and every result is measured in `docs/ai-cto/leans-harness.md`. For the raw
documents, use Mail's export and commit the file under `tools/telepathy/exports/`.
