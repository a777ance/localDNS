# Racetrack task (fixed, identical in every mode)

Each lane reads ONE source file and writes ONE findings file. Nothing else.

Lanes (source -> question):
- R1: CLAUDE.md, section "Reply style: Briefing" -> list every rule that has no gate (no hook or check) and say which.
- R2: tools/check-matrix.py -> list any test whose check cannot fail (always passes) and say why.
- R3: tools/check-superfleet.py -> list any function whose behavior is not described in its docstring.
- R4: docs/ai-cto/loop-tick.md -> list any instruction a scheduled session could read two ways.

Findings file: docs/ai-cto/fleet/racetrack/<MODE>/<LANE>.md
Format: one bullet per finding, each with file and line. Zero findings is a valid answer; say so.
Write area: docs/ai-cto/fleet/racetrack/<MODE>/ only. Do not edit any other file.
