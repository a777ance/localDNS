# Racetrack rules

**Preflight before any run (founder rule, 2026-11-12).** Any request for an actual run is preceded by
a thorough preflight and a series of probes, in this order, each one read before the next:

1. Repo state: `git status --short` is empty, and `leader` matches `origin/leader`.
2. Matrix probes: `python3 tools/matrix.py orient.probe`, `decide.probe`, and `observe.probe push` if the run pushes.
3. Gates: `tools/check-cardinal.py`, `tools/check-matrix.py`, `tools/check-superfleet.py`, `tools/racetrack.py --selftest`.
4. Task file: the mode's task is present and its lanes match the source files that exist.
5. Agents: `ListAgents` shows no subagent still running from an earlier mode.
6. Cost: the number of agent runs and the mode are stated before the first one starts.

Only when all six pass does a run start. A failed step is reported as FAILED, with its output, and the run waits.
