#!/usr/bin/env python3
"""Render the AI Governance Blueprint as a self-contained GitHub Pages page.

Career-facing artifact: maps this homelab's hands-on AI work onto the governance
a regulated insurance MGA expects of a production AI stack. Content lives here as
Python data (single source of truth) and renders to a standalone HTML file under
docs/statements/ so GitHub Pages serves it at a first-party URL:

    https://a777ance.github.io/localDNS/ai-governance-blueprint.html

Company names, individuals, and role specifics are MASKED as [COMPANY]/[CTO]/
[CIO]/[ROLE] to keep this artifact non-confidential. Fill them in privately; do
not commit real identifiers.

No third-party dependencies — stdlib only. Run:  python3 generate_governance.py
"""

import base64
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "ai-governance-blueprint.html")

FONT = "'Gill Sans MT','Gill Sans',Calibri,'Trebuchet MS',sans-serif"

# ───────── content (single source of truth) ─────────

MASKED = ["[COMPANY]", "[CTO]", "[CIO]", "[ROLE]"]

MASTHEAD = dict(
    kicker="Career artifact · masked",
    title="AI Governance Blueprint",
    subtitle="From vibe coding to enterprise guardrails",
    role="[ROLE] · applied AI engineering",
    company="[COMPANY] · a regulated insurance MGA",
    stack="Claude (Anthropic) via AWS Bedrock",
)

# Ordered newest/most-critical first where the source list has an order; the
# frameworks list is alphabetical and therefore runs Z→A per house style.
LEADERSHIP = [
    ("[CTO] — CTO", "Leads application development, analytics, and technology-related "
                    "business engagement."),
    ("[CIO] — CIO", "Oversees the firm's technology infrastructure, operations, and "
                    "enterprise support."),
]

SECTIONS = [
    dict(
        n="1", id="context", title="The context: MGA dynamics & delegated authority",
        lede="An MGA is not a standard software company; it operates under "
             "<b>Delegated Underwriting Authority (DUA)</b>. The job balances the "
             "aggressive growth culture of a wholesale broker against the strict "
             "compliance that capacity providers (carriers / syndicates) require.",
        body="Governance here means protecting the MGA's most valuable asset: "
             "<b>carrier trust</b>. If an AI &ldquo;black box&rdquo; makes an "
             "unexplainable underwriting decision, or hallucinates coverage, the "
             "carrier pulls the pen and the product dies.",
        sub="Essential industry frameworks (mandatory reading)",
        # Alphabetical → Z→A (NY, NIST, NAIC, Lloyd's, Colorado).
        items=[
            ("NY DFS Circular Letter on AI",
             "The most aggressive state-regulator guidance on AI cybersecurity and data privacy."),
            ("NIST AI Risk Management Framework (AI RMF 1.0)",
             "The gold standard for governing AI (Govern, Map, Measure, Manage)."),
            ("NAIC Model Bulletin on AI",
             "Dictates how state departments of insurance view AI testing, bias mitigation, "
             "and third-party vendor risk."),
            ("Lloyd's of London Code of Practice (Delegated Authority)",
             "The global gold standard for how capacity providers expect MGAs to be "
             "governed and audited."),
            ("Colorado SB21-169",
             "The most critical state-level legislation, focused explicitly on preventing "
             "algorithmic discrimination and proxy bias in insurance underwriting."),
        ],
    ),
    dict(
        n="2", id="trust", title="Operationalizing &ldquo;trust but verify&rdquo;",
        lede="Third-party APIs (like Anthropic) sell security through vendor "
             "marketing. The job is to build the verification mechanism across "
             "three pillars.",
        pillars=[
            ("A. Contractual & data safety", [
                ("Zero Data Retention (ZDR)",
                 "Ensure Enterprise agreements explicitly prohibit training on API payloads."),
                ("Data residency",
                 "Verify processing regions comply with PII/PHI regulations."),
            ]),
            ("B. Security & infrastructure", [
                ("Architecture reviews",
                 "Validate SOC 2 / ISO 27001 certifications and threat-model the API connections."),
                ("Red teaming",
                 "Actively test applications with prompt injections to prevent system-prompt "
                 "or data leaks."),
            ]),
            ("C. Model performance & fairness", [
                ("Shadow testing",
                 "Run the AI alongside a human underwriter in &ldquo;shadow mode&rdquo; to "
                 "mathematically benchmark error rates against ground truth before go-live."),
                ("Drift monitoring",
                 "Continuous pipelines to detect data drift as base models update in the "
                 "background."),
            ]),
        ],
    ),
    dict(
        n="3", id="playbook", title="The Claude (Anthropic) governance playbook",
        lede="The target MGA is heavily invested in AI document extraction for "
             "complex policies (e.g. group medical, PEO). Claude is the heavyweight "
             "for these large-context tasks, but it requires specific governance "
             "constraints.",
        steps=[
            ("Infrastructure (AWS Bedrock)",
             "Deploy Claude via Bedrock (not the public API) to keep calls inside the "
             "corporate VPC. Verify with the infrastructure teams (under the [CIO]) that "
             "AWS CloudWatch is not logging PII/PHI."),
            ("Output (extractive QA)",
             "To prevent plausible hallucinations, enforce prompt architectures that "
             "require Claude to cite the exact page number and verbatim text block from "
             "the policy PDF when making a coverage decision."),
            ("Agentic workflows (HITL sandbox)",
             "If agentic capabilities are used to structure JSON and push to "
             "policy-administration systems, enforce a Human-in-the-Loop (HITL) safeguard "
             "so human approval is required before any database is altered."),
        ],
    ),
    dict(
        n="4", id="matrix", title="The translation matrix: homelab to enterprise",
        lede="Hands-on &ldquo;vibe coding&rdquo; experience is an asset precisely "
             "because it teaches intuitively how models fail. Governance is the "
             "process of formalizing that intuition into auditable engineering systems.",
        matrix=[
            ("Tweaking a prompt in the console until it works.",
             "<b>Prompt versioning & registries</b> — storing prompts in Git via "
             "Langfuse / MLflow.",
             "To prove to auditors exactly which prompt version authorized a risk decision."),
            ("Eye-balling the output to see if it looks correct.",
             "<b>Automated evals</b> — Ragas or &ldquo;LLM-as-a-judge&rdquo; to "
             "mathematically score accuracy.",
             "Human underwriters cannot manually check 10,000 policies; statistical proof "
             "is required."),
            ("Asking Claude to return JSON and hoping it formats right.",
             "<b>Structured-output enforcement</b> — Instructor or Pydantic for schema "
             "validation.",
             "A broken JSON bracket in production crashes the downstream policy-admin system."),
            ("Dropping API keys into an <code>.env</code> file.",
             "<b>IAM & VPC routing</b> — routing calls through Bedrock with strict RBAC.",
             "Essential for data security and protecting policyholder PII/PHI."),
        ],
    ),
    dict(
        n="5", id="tooling", title="The MLOps tooling stack",
        lede="Do not build from scratch. Leverage established tooling for AI governance.",
        items=[
            ("Observability & logging",
             "Langfuse, Helicone, or Datadog LLM (log every prompt, response, latency, "
             "and token count)."),
            ("Guardrails",
             "NeMo Guardrails or Guardrails AI (intercept inputs/outputs to block "
             "restricted data or behaviors)."),
            ("Evaluation frameworks",
             "TruLens or DeepEval (mathematically measure context relevance and faithfulness)."),
        ],
    ),
    dict(
        n="6", id="pitch", title="The pitch",
        lede="Framing the background as an asset (company name masked):",
        quote="My background is heavily hands-on. I've spent my time in the trenches "
              "with Claude, pushing its limits in a homelab environment. Because I've "
              "&lsquo;vibe coded&rsquo; and broken these models a hundred different ways, "
              "I know exactly where their weak points are and what an AI hallucination "
              "looks like before it happens. Now, I want to take that raw intuition and "
              "operationalize it &mdash; building the strict logging, prompt registries, "
              "and automated evals necessary to deploy these tools safely in a highly "
              "regulated E&amp;S environment, fully compliant with frameworks like the "
              "NAIC Model Bulletin, Colorado SB21-169, and NY DFS guidelines.",
    ),
]

# ───────── render helpers ─────────


def defrow(term, desc):
    return (f'<div class="dl-row"><div class="dl-t">{term}</div>'
            f'<div class="dl-d">{desc}</div></div>')


def render_section(s):
    parts = [f'<section class="sec" id="{s["id"]}">',
             f'<div class="sec-num">{s["n"]}</div>',
             f'<h2>{s["title"]}</h2>']
    if s.get("lede"):
        parts.append(f'<p class="lede">{s["lede"]}</p>')
    if s.get("body"):
        parts.append(f'<p>{s["body"]}</p>')
    if s.get("sub"):
        parts.append(f'<h3>{s["sub"]}</h3>')
    if s.get("items"):
        parts.append('<div class="dl">')
        parts += [defrow(t, d) for t, d in s["items"]]
        parts.append('</div>')
    if s.get("pillars"):
        parts.append('<div class="pillars">')
        for name, rows in s["pillars"]:
            parts.append(f'<div class="pillar"><div class="pillar-h">{name}</div><div class="dl">')
            parts += [defrow(t, d) for t, d in rows]
            parts.append('</div></div>')
        parts.append('</div>')
    if s.get("steps"):
        parts.append('<ol class="steps">')
        for t, d in s["steps"]:
            parts.append(f'<li><span class="st-t">{t}.</span> {d}</li>')
        parts.append('</ol>')
    if s.get("matrix"):
        parts.append('<div class="mtable-wrap"><table class="mtable"><thead><tr>'
                     '<th>Homelab (vibe coding)</th>'
                     '<th>MGA production (high-octane governance)</th>'
                     '<th>The governance &ldquo;why&rdquo;</th></tr></thead><tbody>')
        for a, b, c in s["matrix"]:
            parts.append(f'<tr><td>{a}</td><td>{b}</td><td class="why">{c}</td></tr>')
        parts.append('</tbody></table></div>')
    if s.get("quote"):
        parts.append(f'<blockquote class="pitch">{s["quote"]}</blockquote>')
    parts.append('</section>')
    return "\n".join(parts)


def render():
    toc = "\n".join(
        f'<a href="#{s["id"]}"><span class="tn">{s["n"]}</span>'
        f'{s["title"]}</a>' for s in SECTIONS
    )
    lead = "\n".join(
        f'<div class="lead-row"><div class="lead-t">{t}</div>'
        f'<div class="lead-d">{d}</div></div>' for t, d in LEADERSHIP
    )
    sections = "\n".join(render_section(s) for s in SECTIONS)
    m = MASTHEAD

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{m['title']} — {m['subtitle']}</title>
<meta name="description" content="Career-facing blueprint: mapping hands-on homelab AI work onto enterprise AI governance for a regulated insurance MGA. Identifiers masked.">
<meta name="robots" content="noindex">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
:root{{--navy:#13314f;--navy-2:#0e2640;--ink:#1f2733;--bronze:#a9803f;
--bronze-soft:#c6a463;--paper:#fbfaf7;--rule:#e6e2d6;--rule-2:#eceef1;
--muted:#8a93a0;--body:#3a4553;}}
html{{scroll-behavior:smooth;}}
body{{font-family:{FONT};background:#e9ecf0;color:var(--ink);padding:40px 18px;
line-height:1.55;-webkit-font-smoothing:antialiased;}}
.page{{max-width:820px;margin:0 auto;background:var(--paper);
box-shadow:0 6px 40px rgba(0,0,0,0.13);}}
.header{{background:var(--navy);color:#fff;padding:34px 46px 28px;
border-bottom:3px solid var(--bronze);}}
.kicker{{display:inline-block;font-size:9px;letter-spacing:0.18em;
text-transform:uppercase;color:var(--navy-2);background:var(--bronze-soft);
border-radius:4px;padding:3px 9px;font-weight:700;}}
h1{{font-size:31px;font-weight:700;letter-spacing:0.01em;margin:14px 0 4px;}}
.sub{{font-size:14px;color:#9fc0da;letter-spacing:0.02em;}}
.meta{{display:flex;flex-wrap:wrap;gap:26px;margin-top:22px;padding-top:18px;
border-top:1px solid rgba(255,255,255,0.14);}}
.meta div .k{{font-size:9px;letter-spacing:0.16em;text-transform:uppercase;
color:#7e9fbb;}}
.meta div .v{{font-size:13px;margin-top:4px;color:#eef4fa;}}
.notice{{background:#fbf6ea;border-left:3px solid var(--bronze);
padding:13px 46px;font-size:11.5px;color:#6a5a34;}}
.notice b{{color:#4d4225;}}
.notice code{{background:#f1e8d4;border-radius:3px;padding:1px 5px;font-size:11px;}}
.toc{{padding:22px 46px;border-bottom:1px solid var(--rule);}}
.toc-h{{font-size:10px;letter-spacing:0.16em;text-transform:uppercase;
color:var(--muted);margin-bottom:12px;}}
.toc a{{display:flex;gap:12px;align-items:baseline;padding:6px 0;
text-decoration:none;color:var(--navy);font-size:14px;
border-bottom:1px solid var(--rule-2);}}
.toc a:last-child{{border-bottom:none;}}
.toc a:hover{{color:var(--bronze);}}
.tn{{font-size:11px;color:var(--bronze);width:16px;flex-shrink:0;
font-feature-settings:"tnum";}}
.body{{padding:6px 46px 40px;}}
.sec{{padding:28px 0;border-bottom:1px solid var(--rule);position:relative;}}
.sec:last-child{{border-bottom:none;}}
.sec-num{{font-size:11px;letter-spacing:0.14em;color:var(--bronze);
font-weight:700;font-feature-settings:"tnum";}}
h2{{font-size:19px;color:var(--navy);font-weight:700;margin:5px 0 12px;
letter-spacing:0.01em;}}
h3{{font-size:11px;text-transform:uppercase;letter-spacing:0.14em;
color:var(--navy);margin:20px 0 12px;}}
p{{font-size:14px;color:var(--body);margin-bottom:10px;}}
p.lede{{font-size:14.5px;color:#2c3744;}}
b{{color:var(--navy);}}
code{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;
background:#f0ede4;border-radius:3px;padding:1px 5px;color:#5a4a2a;}}
.dl{{display:flex;flex-direction:column;gap:2px;}}
.dl-row{{display:grid;grid-template-columns:210px 1fr;gap:16px;
padding:10px 0;border-bottom:1px solid var(--rule-2);}}
.dl-row:last-child{{border-bottom:none;}}
.dl-t{{font-size:13px;color:var(--navy);font-weight:600;}}
.dl-d{{font-size:13px;color:var(--body);}}
.pillars{{display:flex;flex-direction:column;gap:14px;margin-top:4px;}}
.pillar{{border:1px solid var(--rule);border-left:3px solid var(--bronze);
border-radius:8px;padding:14px 18px;background:#fdfcf9;}}
.pillar-h{{font-size:12px;font-weight:700;color:var(--navy);
letter-spacing:0.04em;margin-bottom:8px;}}
.steps{{list-style:none;counter-reset:none;display:flex;
flex-direction:column;gap:12px;}}
.steps li{{font-size:13.5px;color:var(--body);padding:12px 16px;
border-radius:8px;background:#fdfcf9;border:1px solid var(--rule);}}
.st-t{{color:var(--navy);font-weight:700;}}
.mtable-wrap{{overflow-x:auto;margin-top:6px;}}
.mtable{{width:100%;border-collapse:collapse;min-width:560px;}}
.mtable th{{font-size:9.5px;text-transform:uppercase;letter-spacing:0.08em;
color:var(--muted);font-weight:700;text-align:left;padding:0 12px 10px;
border-bottom:1px solid var(--rule);vertical-align:bottom;}}
.mtable td{{padding:12px;font-size:12.5px;color:var(--body);
border-bottom:1px solid var(--rule-2);vertical-align:top;}}
.mtable td.why{{color:#6a7480;font-style:italic;}}
.mtable tr:last-child td{{border-bottom:none;}}
.pitch{{margin-top:8px;padding:20px 24px;background:var(--navy);color:#eef4fa;
border-radius:10px;border-left:4px solid var(--bronze);font-size:15px;
line-height:1.65;font-style:italic;}}
.footer{{padding:20px 46px 30px;border-top:1px solid var(--rule);
font-size:10.5px;color:var(--muted);}}
@media (max-width:640px){{
  body{{padding:16px 0;}}
  .header,.notice,.toc,.body,.footer{{padding-left:22px;padding-right:22px;}}
  h1{{font-size:25px;}}
  .dl-row{{grid-template-columns:1fr;gap:2px;}}
}}
</style>
</head>
<body>
<main class="page">
  <header class="header">
    <span class="kicker">{m['kicker']}</span>
    <h1>{m['title']}</h1>
    <div class="sub">{m['subtitle']}</div>
    <div class="meta">
      <div><div class="k">Target role</div><div class="v">{m['role']}</div></div>
      <div><div class="k">Target company</div><div class="v">{m['company']}</div></div>
      <div><div class="k">Target stack</div><div class="v">{m['stack']}</div></div>
    </div>
  </header>

  <div class="notice">
    <b>Placeholders.</b> Company names, individuals, and role specifics are masked as
    <code>[COMPANY]</code>, <code>[CTO]</code>, <code>[CIO]</code>, and
    <code>[ROLE]</code> to keep this artifact non-confidential. Fill them in privately;
    do not commit real identifiers.
  </div>

  <nav class="toc">
    <div class="toc-h">Contents</div>
    {toc}
    <div style="margin-top:16px;">
      <div class="toc-h">Leadership (masked)</div>
      {lead}
    </div>
  </nav>

  <div class="body">
    {sections}
  </div>

  <footer class="footer">
    Generated from <code>docs/statements/tools/generate_governance.py</code> — the single
    source of truth for this page. Edit the Python, re-run it, and the page rebuilds.
    Long-form companion to the AI-governance line on the resume.
  </footer>
</main>
</body>
</html>
"""


def main():
    out = os.path.normpath(OUT)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render())
    # Guard: this artifact must never carry real identifiers. The terms to reject
    # are base64-encoded on purpose — so that scrubbing the leak does not itself
    # write the plaintext names back into the repo. Decoded only at runtime.
    with open(out, encoding="utf-8") as f:
        text = f.read().lower()
    _enc = ["YW13aW5z", "ZGVndXN0YQ==", "am9zaCBzdHJlZXQ=", "Y2xhcmlvbmRvb3I=", "enl3YXZl"]
    banned = [base64.b64decode(t).decode() for t in _enc]
    if [b for b in banned if b in text]:
        raise SystemExit("REFUSING to write — an unmasked identifier is present.")
    print(f"wrote {out}  ({len(render())} bytes)")
    print(f"masked tokens in use: {', '.join(MASKED)}")


if __name__ == "__main__":
    main()
