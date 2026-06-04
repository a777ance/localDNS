import os, json, random
HERE = os.path.dirname(os.path.abspath(__file__))

# ───────── data-driven pipeline ─────────
# The portfolio statement renders from ../data/portfolio.json. On first run the sample
# book below is seeded to that file; thereafter rendering reads JSON. The fleet roll-up
# step of the collector overwrites portfolio.json from the per-home client JSON files.
DATA = os.path.join(HERE, "..", "data", "portfolio.json")
OUT  = os.path.join(HERE, "..", "operator", "alliance-member-portfolio.html")
DOT  = {"green":"#3f7a4d", "amber":"#c08a2e", "watch":"#2d6aa8"}


def sample_portfolio():
    """Built-in sample book of 20 homes (deterministic)."""
    random.seed(77)
    ARCH = ["Prime-Time", "Home Office", "Connected Family"]
    names = ["Bennett","Chen","Okafor Family","Delgado","Park Household","Nguyen","Brooks","Romano",
             "Haddad","Ferreira","Whitlock","Osei","Sandberg","Cruz","Tanaka","Mbeki",
             "Lindqvist","Patel","Dubois","Reyes Loft"]
    roster = []
    for i, nm in enumerate(names):
        roster.append(dict(acct=f"A77-{i+1:03d}", home=nm, arch=ARCH[i % 3],
                           blocked=random.randint(4,18)*1000 + random.randint(0,999),
                           uptime=random.choice([99.99,99.98,99.97,99.95,99.93,99.9,99.88]),
                           status="green"))
    roster[4]["status"]  = "amber"   # Park Household
    roster[19]["status"] = "amber"   # Reyes Loft
    roster[10]["status"] = "watch"   # Whitlock
    total = sum(r["blocked"] for r in roster)
    healthy   = sum(1 for r in roster if r["status"] == "green")
    attention = sum(1 for r in roster if r["status"] == "amber")
    return dict(
        member=dict(name="Jose Marin", id="ALY-0042", homes=20,
                    period="May 2026", stmt_date="June 1, 2026"),
        kpis=dict(homes=20, threats_blocked=total, avg_uptime="99.9%", attention=attention,
                  healthy=healthy, watch=1),
        attention=[
            dict(sev="high", label="High", acct="A77-020", home="Reyes Loft", arch="Home Office",
                 detail="Appliance storage at <b>88%</b> — query logs growing faster than expected. Left unattended, logging could stall within ~9 days.",
                 meta="Owned by <span class='who'>Jose</span> · cleanup scheduled tonight 02:00 · client not affected yet"),
            dict(sev="med", label="Med", acct="A77-005", home="Park Household", arch="Connected Family",
                 detail="One of three Wi-Fi points is <b>dropping nightly around 1 a.m.</b> and self-recovering. Looks like a failing unit, not config.",
                 meta="Owned by <span class='who'>Jose</span> · replacement unit en route · ETA Jun 3"),
            dict(sev="low", label="Watch", acct="A77-011", home="Whitlock", arch="Prime-Time",
                 detail="WireGuard key is <b>over a year old</b>. No issue today, but worth rotating on the next visit for good hygiene.",
                 meta="Flagged by the system · no action needed this month"),
        ],
        log=[
            dict(scope="20 / 20", text="Rolled out <b>Cloudflare's encrypted-DNS update (v2026.5)</b> to every home the day it shipped. No client saw a hiccup."),
            dict(scope="20 / 20", text="Closed a <b>router-service security flaw (CVE-2026-3118)</b> across all appliances the morning it was disclosed."),
            dict(scope="20 / 20", text="Refreshed ad &amp; tracker blocklists fleet-wide — <b>+4,100 new domains</b>."),
            dict(scope="3 homes", text="Onboarded <b>7 new devices</b> (tablets, a console, two smart-home hubs) onto secure networks."),
            dict(scope="2 homes", text="<b>Proactive hardware swaps</b> — power adapters reading flaky at A77-014 and A77-006, replaced before failure."),
            dict(scope="1 home", text="Re-pointed DNS at A77-001 mid-stream during a Spectrum routing change — <b>zero downtime</b>."),
        ],
        roster=roster,
    )


def attention_html(items):
    out = ""
    for a in items:
        out += (f'<div class="ai {a["sev"]}"><div class="sev">{a["label"]}</div><div class="body2">'
                f'<div class="h">{a["acct"]} · {a["home"]} <span style="color:#8a93a0;font-weight:400">({a["arch"]})</span></div>'
                f'<div class="d">{a["detail"]}</div><div class="meta">{a["meta"]}</div></div></div>')
    return out


def log_html(items):
    return "".join(f'<div class="lx"><div class="scope">{l["scope"]}</div>'
                   f'<div class="txt">{l["text"]}</div></div>' for l in items)


def roster_html(rows):
    out = ""
    for r in rows:
        out += (f'<tr><td><span class="rdot" style="background:{DOT[r["status"]]}"></span></td>'
                f'<td class="acct">{r["acct"]}</td><td class="nm">{r["home"]}</td>'
                f'<td class="arch">{r["arch"]}</td><td class="fig">{r["blocked"]:,}</td>'
                f'<td class="fig">{r["uptime"]}%</td></tr>')
    return out


STYLE = open(os.path.join(HERE, "operator-style.css")).read()


def build(p):
    m, k = p["member"], p["kpis"]
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A777ance — Alliance Member Portfolio — {m["name"]}</title>
<style>{STYLE}</style></head><body><div class="page">
  <div class="header"><div class="header-top">
    <div class="brandwrap"><div class="monogram"><span>A7</span></div>
      <div><div class="brand">A777ANCE</div><div class="brand-sub">Residential Network Services</div>
        <div class="tag">Alliance Member Portfolio</div></div></div>
    <div class="doc-title"><div class="label">Monthly Portfolio Statement</div>
      <div class="period">{m["period"]}</div></div></div>
    <div class="acct-bar">
      <div class="acct-field"><div class="k">Alliance Member</div><div class="v">{m["name"]}</div></div>
      <div class="acct-field"><div class="k">Member ID</div><div class="v">{m["id"]}</div></div>
      <div class="acct-field"><div class="k">Homes Under Management</div><div class="v">{m["homes"]}</div></div>
      <div class="acct-field"><div class="k">Statement Date</div><div class="v">{m["stmt_date"]}</div></div></div></div>

  <div class="kpis">
    <div class="kpi"><div class="v">{k["homes"]}</div><div class="l">Homes Managed</div></div>
    <div class="kpi"><div class="v">{k["threats_blocked"]:,}</div><div class="l">Threats Blocked (all homes)</div></div>
    <div class="kpi"><div class="v">{k["avg_uptime"]}</div><div class="l">Avg Uptime</div></div>
    <div class="kpi"><div class="v warn">{k["attention"]}</div><div class="l">Homes Need Attention</div></div></div>

  <div class="body">
    <div class="section"><div class="section-head"><div class="section-title">Needs Your Attention</div>
      <div class="section-note">flagged across your book — most urgent first</div></div>
      <div class="att">{attention_html(p["attention"])}</div></div>

    <div class="section"><div class="section-head"><div class="section-title">This Month, Across Your Homes</div>
      <div class="section-note">your work log — what carried your subscription</div></div>
      <div class="log">{log_html(p["log"])}</div></div>

    <div class="section"><div class="section-head"><div class="section-title">Your Homes</div>
      <div class="section-note">{m["homes"]} statements generated &amp; delivered this month</div></div>
      <table class="roster"><thead><tr><th></th><th>Account</th><th>Household</th><th>Profile</th><th class="r">Threats Blocked</th><th class="r">Uptime</th></tr></thead>
      <tbody>{roster_html(p["roster"])}</tbody></table>
      <div class="legend-note">
        <span><span class="rdot" style="background:#3f7a4d"></span>Healthy ({k["healthy"]})</span>
        <span><span class="rdot" style="background:#c08a2e"></span>Needs attention ({k["attention"]})</span>
        <span><span class="rdot" style="background:#2d6aa8"></span>Watch ({k["watch"]})</span>
      </div></div>
  </div>
  <div class="footer"><div class="fb">A777ANCE</div>
    <div>Twenty homes, one view · individual statements bundled &amp; mailed · Member {m["id"]} · hello@a777ance.com</div></div>
</div></body></html>'''


def seed():
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    if not os.path.exists(DATA):
        with open(DATA, "w") as f:
            json.dump(sample_portfolio(), f, indent=2, ensure_ascii=False)
        print("seeded", os.path.relpath(DATA, HERE))


def render():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(DATA) as f:
        p = json.load(f)
    html = build(p)
    with open(OUT, "w") as f:
        f.write(html)
    print("wrote operator portfolio", len(html), "bytes")


if __name__ == "__main__":
    seed()
    render()
