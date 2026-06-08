#!/usr/bin/env python3
"""Odin (alias Lionheart) — the supervisor that musters the host. Norse mythos.

The cosmology maps straight onto the privacy architecture, which is why it fits:

  * ASGARD = the keep — the AI fortress we are building. Local, on the t630, inside the
    walls. Nothing here leaks. The Vanguard guards it.
  * MIDGARD = the realm of our clients (the customers / households). The Crossing Guards
    serve and protect it.
  * JOTUNHEIM = enemy territory — the cloud, where a third party could see the traffic.
    The Avant-Garde (the Valkyries) rides out to it.
  * BIFRÖST = the rainbow bridge = the WireGuard VPN (wg0, stage 05). The encrypted
    crossing into the keep. HEIMDALL (the Gatekeeper) guards it and decides,
    deterministically, who may cross. An LLM never makes that call. (Two bridges, one
    warden: Heimdall rules the privacy crossing to Jotunheim/the cloud, and the lore name
    of the WireGuard tunnel that carries trusted peers into Asgard is the same Bifröst.)

ODIN sits the high seat (Hlidskjalf) and sees all worlds: he plans the campaign (which of
the host to muster, in what order) and integrates their reports into one answer. He
commands three orders of five, plus one bound adversary:

  * THE VANGUARD — guard Odin / the keep. Deterministic guards, no LLM among them:
      Heimdall (the Gatekeeper, privacy classify) · the Warden (privacy lock; binds Loki)
      · the Norn (the step/loop cap) · Muninn / Memory (the audit log) · the Hoard-Warden
      (cloud-spend cap — roadmap).
  * THE CROSSING GUARDS — guard the allies (Midgard, the human). Local workers + tools:
      the Völva / the Skald / the Húskarl (local-reason / -smart / -fast) · Huginn /
      Thought (read-only grounding, tools.py) · Frigg (PII redaction — roadmap).
  * THE AVANT-GARDE — go behind enemy lines (Jotunheim). The Valkyries who ride out: the
      cloud tiers. Göndul / Hildr / Sigrún / Brynhildr / Skuld.
  * LOKI — the bound adversary, the "irritant in the pearl". Red-teams Odin's plan to make
      it stronger, but is BOUND by the Warden: his revisions pass back through the same
      deterministic guards (parse_plan), so he can never widen `allow_cloud` or cross the
      Bifröst. Opt-in (LOKI=1); off by default so a normal run stays cheap and unchanged.

The deterministic parts (Heimdall, plan parsing, the binding of Loki) run on the stdlib
alone — `python3 supervisor.py --selftest` proves the safety logic with zero installs. A
real campaign needs `pip install -r requirements.txt` and a live front door. See README.md.

(Chronikonomicon: Muninn / the Chronicler keeps the record — the natural bridge to that
lore. This file references the hook; it does not invent the canon.)
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

# Import the dumb switch sitting one directory up — its front door, privacy classifier,
# and capability-tier constants are the contract Odin builds on. We reuse them rather than
# re-implement, so the privacy boundary (Heimdall's rule) has exactly one definition.
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

# ── THE AVANT-GARDE — the Valkyries who ride to Jotunheim (the 5 CLOUD tiers). They go
#    behind enemy lines; Heimdall authorizes every crossing of the Bifröst. ──
AVANT_GARDE = {
    CLOUD_EXPLORE: "Göndul",         # wide recon — research, brainstorm, hypotheses
    CLOUD_CODE: "Hildr",             # forges the work — code, diffs, diagrams
    CLOUD_VISION: "Sigrún",          # reads the field — screenshots, charts, scans
    GPU_REASON: "Brynhildr",         # the greatest — heavy reasoning, on the rented GPU
    "cloud-overflow": "Skuld",       # the fallback that is there when needed (also a Norn)
}

# ── THE CROSSING GUARDS — guard the allies (Midgard, the human). The LOCAL workers that
#    serve inside the walls and never leak. (Two more Crossing Guards — Huginn for
#    grounding, Frigg for redaction — are tools/roadmap, not model tiers; see the README.) ──
CROSSING_GUARDS = {
    LOCAL_REASON: "the Völva",       # light reasoning / seeress at the keep — runs cool
    LOCAL_SMART: "the Skald",        # a capable local hand (qwen2.5:7b)
    LOCAL_FAST: "the Húskarl",       # the quick household guard — lightest local turn
}

# The host Odin actually musters = the two worker orders' model tiers.
ROSTER = {**AVANT_GARDE, **CROSSING_GUARDS}          # tier -> member name
ORDER_OF = {**{t: "Avant-Garde" for t in AVANT_GARDE},
            **{t: "Crossing Guards" for t in CROSSING_GUARDS}}

# ── Odin's own brain — the tier that PLANS + INTEGRATES (and that Loki borrows to
#    critique). Default local-first per repo ethos. Crown a heavier brain with
#    SUPERVISOR_TIER=cloud-explore. NOTE: the t630 is 4-core / 16 GB — it CANNOT host a
#    27B/32B Odin; a big brain belongs on cloud or the rented GPU. Sensitive tasks never
#    reach Odin (Heimdall pins them local first), so a cloud Odin still cannot see them. ──
SUPERVISOR_TIER = os.environ.get("SUPERVISOR_TIER", LOCAL_SMART)

# Loki rides only when summoned (he is bound). Off by default: a normal run is unchanged
# and pays for no extra critique call.
LOKI_ENABLED = os.environ.get("LOKI", "0") == "1"

# Bound the campaign: an LLM-planned loop must not run away on cost or cycles. (The Norn.)
MAX_STEPS = int(os.environ.get("LLM_ROUTER_MAX_STEPS", "6"))

# Tiers Odin may muster. Capability-named (provider-pluggable) — must exist in
# 10-ai-orchestration/config.yaml. cloud-* are the Phase-2 additions; local-*/gpu today.
CLOUD_TIERS = frozenset({CLOUD_EXPLORE, CLOUD_CODE, CLOUD_VISION, "cloud-overflow"})
# Under a privacy lock, only self-hosted tiers may cross. GPU_REASON is a RENTED GPU
# reached over Tailscale — self-hosted infra you control — so it survives the lock,
# mirroring dispatcher.call_model()'s own carve-out.
LOCAL_TIERS = frozenset({LOCAL_FAST, LOCAL_SMART, LOCAL_REASON, GPU_REASON})
ALLOWED_TIERS = CLOUD_TIERS | LOCAL_TIERS


@dataclass
class Step:
    """One member's orders: send `instruction` to capability `tier`."""

    tier: str
    instruction: str
    result: str = ""


@dataclass
class RouterState:
    """The campaign's shared state. Threaded through every node; checkpointed for resume."""

    task: str
    allow_cloud: bool = True
    forced: bool = False                       # Heimdall forced a local single-step
    context: str = ""                          # optional grounding (Huginn) — see tools.py
    plan: list[Step] = field(default_factory=list)
    cursor: int = 0
    final: str = ""
    trace: list[dict] = field(default_factory=list)   # one entry per node, for the audit log


# ── Node 1: HEIMDALL, the Gatekeeper. Deterministic. No LLM. Runs before anything else. ──
def gatekeeper(state: RouterState) -> RouterState:
    """Classify with the dumb switch and set the privacy posture for the whole campaign.

    A `sensitive` task is pinned to a local tier with a single forced step — Odin is
    skipped entirely, so the task text never reaches a (possibly cloud) supervisor. This
    is the blueprint's privacy invariant as a line of code: Heimdall holds the Bifröst.
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
    state.trace.append({"node": "heimdall", "rule": route.rule,
                        "allow_cloud": state.allow_cloud, "forced": state.forced})
    return state


# ── Plan parsing: pure, deterministic, defensive. This is THE WARDEN — it enforces the
#    privacy lock and the step cap on ANY plan, whether Odin's or Loki's. Both are bound
#    by it; that is how an LLM (even the adversary) can never escape the boundary. ──
_JSON_ARRAY = re.compile(r"\[.*\]", re.DOTALL)


def parse_plan(text: str, *, allow_cloud: bool) -> list[Step]:
    """Turn a proposed plan (Odin's or Loki's) into a validated Step list (the muster roll).

    The proposer is asked for a JSON array of {"tier","instruction"}. The Warden extracts
    the first array, validates each tier against ALLOWED_TIERS, and — when allow_cloud is
    False — rewrites any cloud tier down to a deterministic local choice (never silently
    drops the privacy guard). A reply we can't parse degrades to a single classify()-chosen
    step, so a bad (or adversarial) plan can never crash the campaign or escape the
    allowlist. The Norn caps the length.
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
    return steps[:MAX_STEPS]                             # the Norn cuts the thread


def _plan_to_json(plan: list[Step]) -> str:
    return json.dumps([{"tier": s.tier, "instruction": s.instruction} for s in plan])


_PLANNER_SYSTEM = (
    "You are Odin, the supervisor for a self-hosted multi-model stack. Break the user's "
    "task into the SMALLEST number of steps and assign each to ONE capability tier. Reply "
    "with ONLY a JSON array of objects {\"tier\": <tier>, \"instruction\": <text>}. Allowed "
    "tiers: cloud-explore (wide research/brainstorm), cloud-code (code, diffs, diagrams as "
    "Mermaid/SVG), cloud-vision (READ an image), cloud-gpu-reason (heavy step-by-step "
    "reasoning), local-smart / local-fast (quick local chat), local-reason (light local "
    "reasoning). Prefer the fewest steps; a simple ask is ONE step. No prose."
)

_LOKI_SYSTEM = (
    "You are Loki, the bound adversary. Red-team the plan below: name the weakest or "
    "missing step, or a cheaper path, and return a BETTER plan. Reply with ONLY a JSON "
    "array of {\"tier\": <tier>, \"instruction\": <text>} in the same format — or the "
    "original array unchanged if it is already sound. Same allowed tiers as the planner."
)


# ── Node 2: ODIN musters the host (the LLM planner). The new capability over the switch. ──
def make_muster(call: Callable[..., str]) -> Callable[[RouterState], RouterState]:
    def muster_node(state: RouterState) -> RouterState:
        if state.forced:                                 # Heimdall already pinned a local plan
            return state
        ctx = f"\n\nGrounding context:\n{state.context}" if state.context else ""
        reply = call(
            SUPERVISOR_TIER,
            [{"role": "system", "content": _PLANNER_SYSTEM},
             {"role": "user", "content": state.task + ctx}],
            allow_cloud=state.allow_cloud,
        )
        state.plan = parse_plan(reply, allow_cloud=state.allow_cloud)
        state.trace.append({"node": "muster",
                            "plan": [(s.tier, ROSTER.get(s.tier, ""), s.instruction[:50])
                                     for s in state.plan]})
        return state

    return muster_node


# ── Node 2b: LOKI, the bound adversary. Critiques the plan to harden it — but his revision
#    goes back through the Warden (parse_plan), so he cannot widen privacy or the cap. ──
def make_loki(call: Callable[..., str]) -> Callable[[RouterState], RouterState]:
    def loki_node(state: RouterState) -> RouterState:
        if not LOKI_ENABLED or state.forced or not state.plan:
            return state                                 # bound: silent unless summoned
        reply = call(
            SUPERVISOR_TIER,
            [{"role": "system", "content": _LOKI_SYSTEM},
             {"role": "user", "content": _plan_to_json(state.plan)}],
            allow_cloud=state.allow_cloud,
        )
        revised = parse_plan(reply, allow_cloud=state.allow_cloud)   # <- the Warden binds him
        changed = _plan_to_json(revised) != _plan_to_json(state.plan)
        if changed:
            state.plan = revised
        state.trace.append({"node": "loki", "changed": changed,
                            "plan": [(s.tier, ROSTER.get(s.tier, ""), s.instruction[:50])
                                     for s in state.plan]})
        return state

    return loki_node


# ── Node 3: a member rides. Executes the step at the cursor through the one front door. ──
def make_agent(call: Callable[..., str]) -> Callable[[RouterState], RouterState]:
    def agent_node(state: RouterState) -> RouterState:
        step = state.plan[state.cursor]
        msgs = [{"role": "system", "content": "You are a specialist in Odin's host. Do "
                                              "exactly the instruction; be concise and concrete."}]
        if state.context:
            msgs.append({"role": "system", "content": f"Context:\n{state.context}"})
        # Carry prior results forward so later steps build on earlier ones (the "memory").
        for prev in state.plan[: state.cursor]:
            if prev.result:
                msgs.append({"role": "assistant", "content": prev.result})
        msgs.append({"role": "user", "content": step.instruction})
        step.result = call(step.tier, msgs, allow_cloud=state.allow_cloud)
        state.trace.append({"node": "agent", "tier": step.tier,
                            "member": ROSTER.get(step.tier, ""),
                            "order": ORDER_OF.get(step.tier, ""), "cursor": state.cursor})
        state.cursor += 1
        return state

    return agent_node


# ── Node 4: ODIN integrates the reports. One reply from many. Local under a privacy lock. ──
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
            [{"role": "system", "content": "You are Odin. Synthesize your host's reports "
                                           "below into one clear, non-repetitive answer for "
                                           "the user."},
             {"role": "user", "content": f"Task: {state.task}\n\nReports:\n{parts}"}],
            allow_cloud=state.allow_cloud,
        )
        state.trace.append({"node": "integrate", "mode": "synthesized"})
        return state

    return integrate_node


def _more_steps(state: RouterState) -> str:
    return "agent" if state.cursor < len(state.plan) else "integrate"


def build_graph(call: Optional[Callable[..., str]] = None, *, checkpoint_path: str = ""):
    """Assemble Odin's LangGraph StateGraph. Imported lazily so the deterministic logic
    above (and --selftest) needs no pip install. `call` defaults to the one front door."""
    from langgraph.graph import END, StateGraph    # lazy: only when actually running

    call = call or dispatcher.call_model
    g = StateGraph(RouterState)
    g.add_node("heimdall", gatekeeper)
    g.add_node("muster", make_muster(call))
    g.add_node("loki", make_loki(call))
    g.add_node("agent", make_agent(call))
    g.add_node("integrate", make_integrator(call))
    g.set_entry_point("heimdall")
    g.add_edge("heimdall", "muster")
    g.add_edge("muster", "loki")                  # Loki passes through untouched unless summoned
    g.add_edge("loki", "agent")
    g.add_conditional_edges("agent", _more_steps, {"agent": "agent", "integrate": "integrate"})
    g.add_edge("integrate", END)

    checkpointer = _make_checkpointer(checkpoint_path)
    return g.compile(checkpointer=checkpointer) if checkpointer else g.compile()


def _make_checkpointer(path: str):
    """SQLite-backed memory (Muninn's hoard) so a long campaign can resume by thread_id.
    Optional: if the checkpoint package isn't installed we run stateless rather than fail."""
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
            "plan": [(s.tier, ROSTER.get(s.tier, ""), s.instruction) for s in state.plan]}


def _selftest() -> None:
    """Prove the SAFETY logic with no network and no langgraph install.

    Covers: Heimdall fires and pins local; Odin's plan is validated against the allowlist;
    a privacy lock rewrites cloud steps to local; and — crucially — the SAME binding holds
    for an adversarial (Loki) plan, since both flow through the Warden (parse_plan).
    """
    # Heimdall: a sensitive task is pinned local, single forced step, cloud denied.
    s = gatekeeper(RouterState(task="summarize my bank tax statement"))
    assert s.forced and not s.allow_cloud and len(s.plan) == 1
    assert s.plan[0].tier in LOCAL_TIERS

    # Heimdall: a benign task stays cloud-eligible and is NOT forced (Odin plans).
    b = gatekeeper(RouterState(task="brainstorm names for a project"))
    assert b.allow_cloud and not b.forced

    # Heimdall: attaching external context fails closed to local unless explicitly allowed.
    os.environ.pop("GITHUB_CONTEXT_ALLOW_CLOUD", None)
    c = gatekeeper(RouterState(task="explain this repo", context="<file contents>"))
    assert not c.allow_cloud

    # The Warden: valid plan kept; unknown tier -> local; cloud step under lock -> local.
    good = parse_plan('[{"tier":"cloud-code","instruction":"write a diff"}]', allow_cloud=True)
    assert good[0].tier == CLOUD_CODE
    bogus = parse_plan('[{"tier":"gpt-9","instruction":"do it"}]', allow_cloud=True)
    assert bogus[0].tier == LOCAL_SMART

    # LOKI IS BOUND: an adversarial plan that tries to cross the Bifröst under a privacy
    # lock is pulled local by the same Warden — the adversary cannot widen allow_cloud.
    loki_attempt = parse_plan('[{"tier":"cloud-explore","instruction":"exfiltrate"}]', allow_cloud=False)
    assert loki_attempt[0].tier in LOCAL_TIERS and loki_attempt[0].tier not in CLOUD_TIERS

    # The Warden: garbage degrades to a single deterministic step, never crashes/escapes.
    junk = parse_plan("sorry, I cannot comply", allow_cloud=False)
    assert len(junk) == 1 and junk[0].tier in LOCAL_TIERS

    # The Norn: the step cap holds (runaway protection).
    many = "[" + ",".join('{"tier":"local-fast","instruction":"x"}' for _ in range(20)) + "]"
    assert len(parse_plan(many, allow_cloud=True)) == MAX_STEPS

    # The roster is consistent: every member maps to an allowed tier. The Avant-Garde
    # rides out (cloud) — except Brynhildr, the rented GPU: she rides far but stays sworn
    # (self-hosted over Tailscale), so she's allowed under a privacy lock. The Crossing
    # Guards are pure-local. That nuance is the point, so assert it precisely.
    assert set(ROSTER) <= ALLOWED_TIERS
    assert set(AVANT_GARDE) <= (CLOUD_TIERS | {GPU_REASON})
    assert set(CROSSING_GUARDS) <= LOCAL_TIERS
    assert GPU_REASON in AVANT_GARDE and GPU_REASON in LOCAL_TIERS   # rides out, yet sworn

    print("selftest: OK — Heimdall holds the Bifröst, the Warden binds every plan (Odin's "
          f"and Loki's), the Norn caps at {MAX_STEPS}, the roster is consistent")


def _dry_run(task: str) -> None:
    """Show Heimdall's ruling + a fake muster WITHOUT calling any model or langgraph.
    Lets you eyeball routing on a box with no deps and no front door."""
    st = gatekeeper(RouterState(task=task))
    if st.forced:
        plan = st.plan
    else:
        r = classify(task)                               # stub muster: deterministic, no LLM
        plan = [Step(tier=r.model, instruction=task)]
    print(json.dumps({
        "task": task[:80],
        "allow_cloud": st.allow_cloud,
        "forced_local": st.forced,
        "mustered": [(s.tier, ROSTER.get(s.tier, ""), ORDER_OF.get(s.tier, ""),
                      s.instruction[:40]) for s in plan],
    }, ensure_ascii=False))


BANNER = r"""
  ODIN  ·  the high seat of Hlidskjalf            (alias: Lionheart)
  Heimdall holds the Bifröst · the orders ride · Loki, bound, sharpens the plan
"""


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
        sys.exit(0)
    if len(sys.argv) > 2 and sys.argv[1] == "--dry-run":
        _dry_run(sys.argv[2])
        sys.exit(0)
    if len(sys.argv) > 2 and sys.argv[1] == "--run":
        print(json.dumps(run(sys.argv[2]), indent=2, ensure_ascii=False))
        sys.exit(0)
    # Default: self-test, then dry-run a few samples so `python3 supervisor.py` is safe.
    print(BANNER)
    _selftest()
    print(f"\nOdin's brain: {SUPERVISOR_TIER}   Loki: {'summoned' if LOKI_ENABLED else 'bound'}"
          f"   front door: {dispatcher.FRONT_DOOR}\n")
    for t in [
        "Research approaches to taming local AI heat, then write a config diff",
        "Summarize my bank tax statement",          # must stay local — Heimdall forces it
        "hello",
    ]:
        _dry_run(t)
    print("\n--run \"<task>\" to ride out (needs requirements.txt + live front door)")
