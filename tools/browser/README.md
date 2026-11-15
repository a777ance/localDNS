# tools/browser

Python ports of the harness's shell hooks, for places with no bash (the in-browser explorer, or any Windows box).
Each keeps the original's contract; the shell original stays the source of truth on a real machine.

| port | original | notes |
|---|---|---|
| `momentum.py` | `.claude/hooks/momentum.sh` | identical logic and state files |
| `refeed.py` | `.claude/hooks/refeed.sh` | context text is read from the original's heredoc; the sync half reports the snapshot instead of fetching |
| `gate.py` | `.claude/hooks/gate.sh` | under the browser shim, checks that need a real OS are listed as not run |

The explorer maps `settings.json` hook commands ending in `.sh` to the port of the same name here.

## hooks.js and test/

`hooks.js` is a JavaScript port of the Python hooks, for a place with no Python at all (a claude.ai artifact's
security policy blocks the Python runtime download). It covers `decide-act.py` (Stop), `cardinal.py` and `timing.py`
(Pre/PostToolUse), and the `refeed.sh`, `momentum.sh` and `gate.sh` behaviour. The Python and shell hooks stay the
source of truth; the port exists to behave the same.

`test/` proves it. Each script copies the working tree to a temp dir, runs identical inputs through the real Python
hooks and through `hooks.js`, and compares the output exactly:

    node tools/browser/test/parity.js         # targeted cases, state files, timing, refeed, momentum, gate
    node tools/browser/test/fuzz-stop.js      # 400 random replies through decide-act
    node tools/browser/test/fuzz-cardinal.js  # 300 random shell commands through cardinal

Known differences: decide-act's SCRATCH rule is omitted (no scratchpad directory in a browser), the commit gate fails
closed on `git commit` instead of running the checks, and a few regex classes (`\d`, `\b`) are the JS ones.

## explorer/

The source of the repo explorer, the claude.ai artifact that runs these hooks in a browser:
`index.template.html` (the page), `browser_shim.py` (the Python runtime shim, used only where Pyodide can load),
and `build.py`, which embeds `hooks.js` and the shim and writes the page's data from this checkout:

    python3 tools/browser/explorer/build.py /tmp/localdns-explorer

Publish the three files it writes (`index.html`, `repo.json`, `bin.json`) to the artifact. The artifact declares
`sample` and `db`; the mailbox protocol is `tools/telepathy/ARTIFACT-BUS.md`.
