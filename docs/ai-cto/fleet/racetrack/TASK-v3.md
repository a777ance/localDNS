# Racetrack task v3 (fixed; identical for sequential and parallel-8, both runs)

Each lane reads ONE source file and writes ONE findings file. Nothing else.

- R1: CLAUDE.md, section "Reply style: Briefing" -> every rule with no gate (no hook or check); say which.
- R2: tools/check-matrix.py -> any test whose check cannot fail; say why.
- R3: tools/check-superfleet.py -> any function whose behaviour its docstring does not describe.
- R4: docs/ai-cto/loop-tick.md -> any instruction a scheduled session could read two ways.
- R5: docs/ai-cto/prose-rules-audit.md -> any row whose "Measured now" claim has no command that shows it.
- R6: tools/check-decisions.py -> any rule the check enforces that its docstring does not state.
- R7: docs/ai-cto/checkpoint.md -> any fact in the live block that cannot be read from git.
- R8: .claude/hooks/cardinal.py -> any branch that can raise and so fail open silently.

Findings file: docs/ai-cto/fleet/racetrack/<MODE-RUN>/<LANE>.md
Format:
- The first line is "# <LANE> findings".
- Then a line "Count: N".
- Then ONLY findings, each as one bullet "- " with file and line. Nothing else is a bullet.
- Anything that is not a finding goes under a heading "## Notes" at the end, written as plain
  paragraphs with NO bullets.
- Zero findings is a valid answer: write "Count: 0".
Quote the file and line for every finding. Do not guess a line number.
Write area: docs/ai-cto/fleet/racetrack/<MODE-RUN>/ only. Edit nothing else.
