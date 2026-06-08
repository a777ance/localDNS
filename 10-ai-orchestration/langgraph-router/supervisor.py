#!/usr/bin/env python3
"""LangGraph supervisor — the LLM-PLANNED, stateful layer above the dumb switch.

This is the "optional later" path the ORCHESTRATION-BLUEPRINT named (§3): when a flat
scripted pipeline isn't enough and you want a brain that PLANS a multi-step workflow,
recruits specialist tiers, keeps state across steps, and integrates the results.

What this is, and — just as important — what it is NOT:

  * It does NOT reopen the decided invariant "no LLM decides the privacy route."
    The privacy gate is still deterministic Python: `dispatcher.classify()` runs FIRST,
    before any LLM sees the task. A task classified `sensitive` is pinned to a local
    tier with allow_cloud=False and the supervisor never plans it — the LLM cannot
    out-vote the privacy lock. (See gate() and the blueprint §4.2.)
  * The LLM's job is PLANNING and INTEGRATION (which specialists, in what order, how to
    combine them), not the privacy decision. That is the genuinely new capability over
    dispatcher.py and is exactly the "stateful multi-step graphs" use the blueprint
    reserved for LangGraph.
  * Everything still speaks the ONE front door. Workers call dispatcher.call_model()
    against ai.home.lan:4040 — same retries/failover/privacy enforcement as the switch.
    "Route, don't shard" still holds: each tier is a whole model behind LiteLLM.

Runs the deterministic parts (gate, plan parsing, tier validation) on stdlib alone, so
`python3 supervisor.py --selftest` proves the safety logic with zero pip installs. The
actual graph run needs `pip install -r requirements.txt` (langgraph) and a live front
door. See README.md in this folder.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

# Import the dumb switch sitting one directory up — its front door, privacy classifier,
# and capability-tier constants are the contract this layer builds on. We reuse them
# rather than re-implement, so the privacy boundary has exactly one definition.
_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
import dispatcher  # noqa: E402  (path set above)
from dispatcher import (  # noqa: E402
    CLOUD_CODE,
    CLOUD_EXPLORE,
    CLOUD_VISION,
    GPU_REASON,
    LOCAL_FAST,
    LOCAL_REASON,
    classify,
)

LOCAL_SMART = "local-smart"  # qwen2.5:7b on the t630 — dispatcher doesn't name it; we do

# ── Which model does the PLANNING / INTEGRATION. Default local-first per repo ethos
#    (local is the privacy-preserving default; cloud is overflow). Planning is light, so
#    a local 7B is a fine cheap brain. Switch to cloud-explore for harder planning —
#    one env var, no code change. Sensitive tasks NEVER reach this tier (gate() pins
#    them local before the supervisor runs), so a cloud supervisor still can't see them.
SUPERVISOR_TIER = os.environ.get("SUPERVISOR_TIER", LOCAL_SMART)

# Bound the graph: an LLM-planned loop must not run away on cost or cycles.
MAX_STEPS = int(os.environ.get("LLM_ROUTER_MAX_STEPS", "6"))

# Tiers the planner may target. Capability-named (provider-pluggable) — must exist in
# 10-ai-orchestration/config.yaml. cloud-* are the Phase-2 additions; local-*/gpu are today.
CLOUD_TIERS = frozenset({CLOUD_EXPLORE, CLOUD_CODE, CLOUD_VISION, "cloud-overflow"})
# Under a privacy lock, only self-hosted tiers are allowed. GPU_REASON is a RENTED GPU
# reached over Tailscale — self-hosted infra you control — so it survives the lock,
# mirroring dispatcher.call_model()'s own carve-out.
LOCAL_TIERS = frozenset({LOCAL_FAST, LOCAL_SMART, LOCAL_REASON, GPU_REASON})
ALLOWED_TIERS = CLOUD_TIERS | LOCAL_TIERS


@dataclass
class Step:
    """One node of work the planner scheduled: send `instruction` to capability `tier`."""

    tier: str
    instruction: str
    result: str = ""


@dataclass
class RouterState:
    """The graph's shared state. Threaded through every node; checkpointed for resume."""

    task: str
    allow_cloud: bool = True
    forced: bool = False                       # privacy gate forced a local single-step
    context: str = ""                          # optional grounding (e.g. GitHub) — see tools.py
    plan: list[Step] = field(default_factory=list)
    cursor: int = 0
    final: str = ""
    trace: list[dict] = field(default_factory=list)   # one entry per node, for the audit log


# ── Node 1: the DETERMINISTIC privacy gate. No LLM. Runs before anything else. ──
def gate(state: RouterState) -> RouterState:
    """Classify with the dumb switch and set the privacy posture for the whole run.

    A `sensitive` task is pinned to a local tier with a single forced step — the planner
    is skipped entirely so the task text never reaches a (possibly cloud) supervisor.
    This is the blueprint's privacy invariant as a line of code, not a hope.
    """
    route = classify(state.task)
    state.allow_cloud = route.allow_cloud
    if route.rule == "sensitive":
        state.forced = True
        state.plan = [Step(tier=route.model, instruction=state.task)]
    # If the caller attached external context (e.g. a private repo), fail closed to local
    # unless explicitly allowed — fetched repo content can be private; don't ship it to
    # cloud on a guess. Opt in with GITHUB_CONTEXT_ALLOW_CLOUD=1 when the source is public.
    if state.context and os.environ.get("GITHUB_CONTEXT_ALLOW_CLOUD", "0") != "1":
        state.allow_cloud = False
    state.trace.append({"node": "gate", "rule": route.rule, "allow_cloud": state.allow_cloud,
                        "forced": state.forced})
    return state


# ── Plan parsing: pure, deterministic, defensive. The LLM proposes; this disposes. ──
_JSON_ARRAY = re.compile(r"\[.*\]", re.DOTALL)


def parse_plan(text: str, *, allow_cloud: bool) -> list[Step]:
    """Turn the planner's reply into a validated Step list.

    The planner is asked for a JSON array of {"tier","instruction"}. We extract the first
    array, validate each tier against ALLOWED_TIERS, and — when allow_cloud is False —
    rewrite any cloud tier down to a deterministic local choice (never silently drop the
    privacy guard). A reply we can't parse degrades to a single classify()-chosen step,
    so a bad plan can never crash the run or escape the tier allowlist.
    """
    steps: list[Step] = []
    m = _JSON_ARRAY.search(text or "")
    if m:
        try:
            raw = json.loads(m.group(0))
        except json.JSONDecodeError:
            raw = []
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            tier = str(item.get("tier", "")).strip()
            instr = str(item.get("instruction", "")).strip()
            if not instr:
                continue
            if tier not in ALLOWED_TIERS:
                tier = LOCAL_SMART                       # unknown tier -> safe local default
            if not allow_cloud and tier in CLOUD_TIERS:
                tier = LOCAL_REASON                      # privacy lock: pull cloud step local
            steps.append(Step(tier=tier, instruction=instr))
    if not steps:                                        # unparseable -> deterministic fallback
        route = classify(text)
        tier = route.model if (allow_cloud or route.model in LOCAL_TIERS) else LOCAL_REASON
        steps.append(Step(tier=tier, instruction=text))
    return steps[:MAX_STEPS]


_PLANNER_SYSTEM = (
    "You are a routing supervisor for a self-hosted multi-model stack. Break the user's "
    "task into the SMALLEST number of steps and assign each to ONE capability tier. "
    "Reply with ONLY a JSON array of objects {\"tier\": <tier>, \"instruction\": <text>}. "
    "Allowed tiers: cloud-explore (wide research/brainstorm), cloud-code (code, diffs, "
    "diagrams as Mermaid/SVG), cloud-vision (READ an image), cloud-gpu-reason (heavy "
    "step-by-step reasoning), local-smart / local-fast (quick local chat), local-reason "
    "(light local reasoning). Prefer the fewest steps; a simple ask is ONE step. No prose."
)


# ── Node 2: the LLM PLANNER. The genuinely new capability over dispatcher.py. ──
def make_planner(call: Callable[..., str]) -> Callable[[RouterState], RouterState]:
    def plan_node(state: RouterState) -> RouterState:
        if state.forced:                                 # gate already pinned a local plan
            return state
        ctx = f"\n\nGrounding context:\n{state.context}" if state.context else ""
        reply = call(
            SUPERVISOR_TIER,
            [{"role": "system", "content": _PLANNER_SYSTEM},
             {"role": "user", "content": state.task + ctx}],
            allow_cloud=state.allow_cloud,
        )
        state.plan = parse_plan(reply, allow_cloud=state.allow_cloud)
        state.trace.append({"node": "plan", "steps": [(s.tier, s.instruction[:60]) for s in state.plan]})
        return state

    return plan_node


# ── Node 3: WORKER. Executes the step at the cursor through the one front door. ──
def make_worker(call: Callable[..., str]) -> Callable[[RouterState], RouterState]:
    def worker_node(state: RouterState) -> RouterState:
        step = state.plan[state.cursor]
        msgs = [{"role": "system", "content": "You are a specialist worker. Do exactly the "
                                              "instruction; be concise and concrete."}]
        if state.context:
            msgs.append({"role": "system", "content": f"Context:\n{state.context}"})
        # Carry prior results forward so later steps build on earlier ones (the "memory").
        for prev in state.plan[: state.cursor]:
            if prev.result:
                msgs.append({"role": "assistant", "content": prev.result})
        msgs.append({"role": "user", "content": step.instruction})
        step.result = call(step.tier, msgs, allow_cloud=state.allow_cloud)
        state.trace.append({"node": "worker", "tier": step.tier, "cursor": state.cursor})
        state.cursor += 1
        return state

    return worker_node


# ── Node 4: INTEGRATE. One reply from many partials. Stays local under a privacy lock. ──
def make_integrator(call: Callable[..., str]) -> Callable[[RouterState], RouterState]:
    def integrate_node(state: RouterState) -> RouterState:
        if len(state.plan) == 1:                         # nothing to stitch
            state.final = state.plan[0].result
            state.trace.append({"node": "integrate", "mode": "passthrough"})
            return state
        parts = "\n\n".join(f"[{s.tier}] {s.result}" for s in state.plan if s.result)
        tier = SUPERVISOR_TIER if (state.allow_cloud or SUPERVISOR_TIER in LOCAL_TIERS) else LOCAL_REASON
        state.final = call(
            tier,
            [{"role": "system", "content": "Synthesize the specialist outputs below into one "
                                           "clear, non-repetitive answer for the user."},
             {"role": "user", "content": f"Task: {state.task}\n\nSpecialist outputs:\n{parts}"}],
            allow_cloud=state.allow_cloud,
        )
        state.trace.append({"node": "integrate", "mode": "synthesized"})
        return state

    return integrate_node


def _has_more_steps(state: RouterState) -> str:
    return "worker" if state.cursor < len(state.plan) else "integrate"


def build_graph(call: Optional[Callable[..., str]] = None, *, checkpoint_path: str = ""):
    """Assemble the LangGraph StateGraph. Imported lazily so the deterministic logic
    above (and --selftest) needs no pip install. `call` defaults to the one front door."""
    from langgraph.graph import END, StateGraph    # lazy: only when actually running

    call = call or dispatcher.call_model
    g = StateGraph(RouterState)
    g.add_node("gate", gate)
    g.add_node("plan", make_planner(call))
    g.add_node("worker", make_worker(call))
    g.add_node("integrate", make_integrator(call))
    g.set_entry_point("gate")
    g.add_edge("gate", "plan")
    g.add_edge("plan", "worker")
    g.add_conditional_edges("worker", _has_more_steps, {"worker": "worker", "integrate": "integrate"})
    g.add_edge("integrate", END)

    checkpointer = _make_checkpointer(checkpoint_path)
    return g.compile(checkpointer=checkpointer) if checkpointer else g.compile()


def _make_checkpointer(path: str):
    """SQLite-backed memory so a long multi-step run can resume by thread_id. Optional:
    if the checkpoint package isn't installed we run stateless rather than failing."""
    path = path or os.environ.get("LLM_ROUTER_CHECKPOINT", "")
    if not path:
        return None
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        return SqliteSaver.from_conn_string(os.path.expanduser(path))
    except Exception:                                    # dep missing / unusable -> stateless
        return None


def run(task: str, *, context: str = "", thread_id: str = "default") -> dict:
    """End-to-end: build the graph and invoke it. Needs langgraph + a live front door."""
    graph = build_graph()
    init = RouterState(task=task, context=context)
    config = {"configurable": {"thread_id": thread_id}}
    out = graph.invoke(init, config=config)
    state = out if isinstance(out, RouterState) else RouterState(**out)
    return {"final": state.final, "trace": state.trace,
            "plan": [(s.tier, s.instruction) for s in state.plan]}


def _selftest() -> None:
    """Prove the SAFETY logic with no network and no langgraph install.

    Covers: the deterministic privacy gate fires and pins local; the planner output is
    validated against the tier allowlist; and a privacy lock rewrites cloud steps to
    local — the three places the LLM could otherwise escape the boundary.
    """
    # gate: a sensitive task is pinned local, single forced step, cloud denied.
    s = gate(RouterState(task="summarize my bank tax statement"))
    assert s.forced and not s.allow_cloud and len(s.plan) == 1
    assert s.plan[0].tier in LOCAL_TIERS

    # gate: a benign task stays cloud-eligible and is NOT forced (planner will run).
    b = gate(RouterState(task="brainstorm names for a project"))
    assert b.allow_cloud and not b.forced

    # gate: attaching external context fails closed to local unless explicitly allowed.
    os.environ.pop("GITHUB_CONTEXT_ALLOW_CLOUD", None)
    c = gate(RouterState(task="explain this repo", context="<file contents>"))
    assert not c.allow_cloud

    # parse_plan: valid plan kept; unknown tier -> local; cloud step under lock -> local.
    good = parse_plan('[{"tier":"cloud-code","instruction":"write a diff"}]', allow_cloud=True)
    assert good[0].tier == CLOUD_CODE
    bogus = parse_plan('[{"tier":"gpt-9","instruction":"do it"}]', allow_cloud=True)
    assert bogus[0].tier == LOCAL_SMART
    locked = parse_plan('[{"tier":"cloud-explore","instruction":"research"}]', allow_cloud=False)
    assert locked[0].tier in LOCAL_TIERS and locked[0].tier not in CLOUD_TIERS

    # parse_plan: garbage degrades to a single deterministic step, never crashes/escapes.
    junk = parse_plan("sorry, I cannot comply", allow_cloud=False)
    assert len(junk) == 1 and junk[0].tier in LOCAL_TIERS

    # parse_plan: respects the step cap (runaway protection).
    many = "[" + ",".join('{"tier":"local-fast","instruction":"x"}' for _ in range(20)) + "]"
    assert len(parse_plan(many, allow_cloud=True)) == MAX_STEPS

    print("selftest: OK — privacy gate pins local, plan validated, lock pulls cloud→local, "
          f"steps capped at {MAX_STEPS}")


def _dry_run(task: str) -> None:
    """Show the gate decision + a fake plan WITHOUT calling any model or langgraph.
    Lets you eyeball routing on a box with no deps and no front door."""
    st = gate(RouterState(task=task))
    if st.forced:
        plan = st.plan
    else:
        # stub planner: deterministic classify, so dry-run needs no LLM
        r = classify(task)
        plan = [Step(tier=r.model, instruction=task)]
    print(json.dumps({
        "task": task[:80],
        "allow_cloud": st.allow_cloud,
        "forced_local": st.forced,
        "planned": [(s.tier, s.instruction[:60]) for s in plan],
    }))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
        sys.exit(0)
    if len(sys.argv) > 2 and sys.argv[1] == "--dry-run":
        _dry_run(sys.argv[2])
        sys.exit(0)
    if len(sys.argv) > 2 and sys.argv[1] == "--run":
        print(json.dumps(run(sys.argv[2]), indent=2))
        sys.exit(0)
    # Default: self-test, then dry-run a few samples so `python3 supervisor.py` is safe.
    _selftest()
    print(f"\nsupervisor tier: {SUPERVISOR_TIER}   front door: {dispatcher.FRONT_DOOR}\n")
    for t in [
        "Research approaches to taming local AI heat, then write a config diff",
        "Summarize my bank tax statement",          # must stay local — forced
        "hello",
    ]:
        _dry_run(t)
    print("\n--run \"<task>\" to execute the graph (needs requirements.txt + live front door)")
