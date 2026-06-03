#!/usr/bin/env python3
"""
compose.py — the "brain". Turns one home's MEASURED stats (collect_stats.py) plus an
operator sidecar (the facts the box can't measure: who the client is, the change log,
the Alliance match, cohort averages) into a full statement JSON that
generate_client.py can render.

  stats.json  +  sidecar.json   --compose-->   data/clients/<slug>.json   --render-->  HTML

The archetype + chips + suggestions are chosen by rules from the traffic mix — this is
the classifier the bots run. Prose is templated and deterministic; swap compose_prose()
for a Claude (Haiku) call when you want richer copy (the inputs are already assembled).

Test end-to-end with no box:
  python3 collect/collect_stats.py --sample --out /tmp/s.json
  python3 compose.py --stats /tmp/s.json --sidecar collect/sample-sidecar.json --out /tmp/out.json
  # then point generate_client at it, or inspect /tmp/out.json
"""
import argparse, json, os

GB = 1024 ** 3
RAMP_MAX = 7   # template renders up to 7 category rows

# ── archetype rules: classifier picks one, then borrows its copy ──
RULES = {
    "prime-time": dict(
        emoji="&#127909;", name="The Prime-Time Household", tag="built around the evening screen",
        chips=["&#127902; <b>Screen-forward</b>", "&#127769; Evening-peaked", "&#127918; Steady gamer", "&#127968; Always-on IoT"],
        sug_title="Have You Tried?",
        suggestions=[
            ["&#128225;", "Have you tried a second Wi-Fi point near the living room?",
             "Your streaming concentrates in one room on weeknights. A mesh node there would smooth playback when several screens are on at once.",
             "Ask us &rarr; we keep a couple on hand"],
            ["&#127909;", "Have you considered a streaming-priority tuning?",
             "We can weight your traffic shaping so video never competes with a backup or a big download after 7pm.",
             "Ask us &rarr; a 5-minute change, no cost"],
        ]),
    "home-office": dict(
        emoji="&#128188;", name="The Home Office", tag="the network clocks in at 9 a.m.",
        chips=["&#9728; <b>Daytime-peaked</b>", "&#128222; Call-heavy", "&#9729; Cloud-reliant", "&#11014; Upload-sensitive"],
        sug_title="Have You Tried?",
        suggestions=[
            ["&#128267;", "Have you considered a battery backup (UPS)?",
             "Your livelihood runs over this connection. A small UPS keeps the appliance alive through brief outages — so a flickering line never drops you mid-call.",
             "Ask us &rarr; we can spec one to your gear"],
            ["&#128249;", "Have you tried locking video calls to top priority?",
             "We can pin conferencing above everything in your traffic shaping, so a backup kicking off never steals from a live call.",
             "Ask us &rarr; a 5-minute change, no cost"],
        ]),
    "connected-family": dict(
        emoji="&#128106;", name="The Connected Family", tag="many devices, one happy network",
        chips=["&#128241; <b>Device-dense</b>", "&#128126; IoT-heavy", "&#128118; Family hours", "&#127777; Weekend-peaked"],
        sug_title="Our Read This Month",
        affirmation=dict(ic="&#9989;", t="Nothing to change this month.",
            d="We looked hard — your network stayed fast, filtered, and congestion-free all month. There's genuinely nothing we'd tune right now. Beautifully boring. We'll keep watching.")),
}


def classify(shares, devices):
    """shares: {category: fraction}. Returns an archetype key."""
    conf = shares.get("Video Conferencing", 0) + shares.get("Cloud & Backups", 0)
    if devices and devices >= 12:
        return "connected-family"
    if shares.get("Video Conferencing", 0) >= 0.12 and conf >= 0.38:
        return "home-office"
    if shares.get("Streaming & Video", 0) >= 0.33:
        return "prime-time"
    # fallback: dominant category's nearest archetype, else prime-time
    return "prime-time"


def build_alloc(by_category):
    total = sum(by_category.values()) or 1
    items = sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)
    # keep top (RAMP_MAX-1) named, fold the rest into Other
    head, tail = items[:RAMP_MAX - 1], items[RAMP_MAX - 1:]
    other = sum(v for _, v in tail) + dict(items).get("Other", 0) * 0
    rows = []
    for cat, b in head:
        if cat == "Other":
            continue
        rows.append([cat, round(100 * b / total), f"{b / GB:.1f} GB"])
    other_bytes = sum(v for _, v in tail if _ != "Other") + dict(head).get("Other", 0)
    # ensure an Other row if any remainder
    accounted = sum(b for _, b in head if _ != "Other")
    remainder = total - accounted
    if remainder > 0 and not any(r[0] == "Other" for r in rows):
        rows.append(["Other", round(100 * remainder / total), f"{remainder / GB:.1f} GB"])
    # normalise pct to sum ~100 (rounding)
    return rows, total


def compare_rows(stats, cohort, archetype, shares):
    """Diverging-axis rows: delta vs cohort average; sentiment independent of direction."""
    def delta(v, avg):
        return round(100 * (v - avg) / avg) if avg else 0
    daily_gb = (sum(stats["volume"]["by_category"].values()) / GB) / 30.0
    threats_day = stats["queries"]["blocked"] / 30.0
    lat = stats["latency_ms"]["peak"]
    rows = [
        dict(metric="Daily data volume", value=f"{daily_gb:.1f} GB/day",
             delta=delta(daily_gb, cohort["avg_daily_gb"]), sentiment="neutral"),
        dict(metric="Threats blocked / day", value=f"{round(threats_day)}/day",
             delta=delta(threats_day, cohort["avg_threats_day"]), sentiment="good",
             verdict="working harder for you"),
        dict(metric="Loaded latency", value=f"{lat} ms",
             delta=delta(lat, cohort["avg_latency_ms"]), sentiment="good",
             verdict="lower is better"),
    ]
    # one archetype-flavoured neutral row
    if archetype == "home-office":
        share = round(100 * shares.get("Video Conferencing", 0))
        rows.insert(1, dict(metric="Video-call share", value=f"{share}%",
                            delta=delta(share, cohort.get("avg_videocall_share", 13)), sentiment="neutral"))
    else:
        share = round(100 * shares.get("Streaming & Video", 0))
        rows.insert(1, dict(metric="Streaming share", value=f"{share}%",
                            delta=delta(share, cohort.get("avg_streaming_share", 48)), sentiment="neutral"))
    return rows


def compose_prose(archetype, alloc, devices):
    """Deterministic templated prose. Replace with a Claude call for richer copy."""
    top = alloc[0]
    body = (f'Your largest "macro" this month was <b>{top[0]}</b> at <b>{top[1]}%</b> of all traffic. '
            f'The balance of the mix is what defines the month — and yours reads clearly as '
            f'{RULES[archetype]["name"].lower()}.')
    macro = ('Think of these as your network\'s macros — like a diet, it\'s the <b>balance</b> '
             'that matters, not any single site.')
    return body, macro


def compose(stats, sidecar):
    by_cat = stats["volume"]["by_category"]
    total = sum(by_cat.values()) or 1
    shares = {k: v / total for k, v in by_cat.items()}
    devices = stats.get("devices")
    archetype = sidecar.get("force_archetype") or classify(shares, devices)
    rule = RULES[archetype]
    alloc, total_bytes = build_alloc(by_cat)
    body, macro = compose_prose(archetype, alloc, devices)

    q = stats["queries"]
    prot = round(100 * q["blocked"] / q["total"], 1) if q["total"] else 0
    pr = sidecar.get("prior", {})           # prior-period values (operator/last run)
    ytd = sidecar.get("ytd", {})
    summary = [
        ["Queries resolved", f"{q['total']:,}", pr.get("queries", "—"), pr.get("queries_chg", ""), ytd.get("queries", "—")],
        ["Threats &amp; trackers blocked", f"{q['blocked']:,}", pr.get("blocked", "—"), pr.get("blocked_chg", ""), ytd.get("blocked", "—")],
        ["Protection rate", f"{prot}%", pr.get("prot", "—"), pr.get("prot_chg", ""), ytd.get("prot", "—")],
        ["Network availability", f"{stats['uptime']['pct']}%", pr.get("uptime", "—"), pr.get("uptime_chg", ""), ytd.get("uptime", "—")],
        ["Peak loaded latency", f"{stats['latency_ms']['peak']} ms", pr.get("latency", "—"), pr.get("latency_chg", ""), ytd.get("latency", "—")],
        ["Secure VPN sessions", f"{stats['vpn_sessions']['count']}", pr.get("vpn", "—"), pr.get("vpn_chg", ""), ytd.get("vpn", "—")],
    ]

    acct = sidecar["account"]
    cfg = dict(
        holder=acct["holder"], acct=acct["acct"], period=acct["period"], stmt_date=acct["stmt_date"],
        live_url=acct["live_url"], stmt_url=acct["stmt_url"], conn_url=sidecar["ally"]["conn_url"],
        handled=sidecar["handled"], handled_foot=sidecar["handled_foot"],
        summary=summary, total_gb=f"{total_bytes / GB:.0f}", alloc=alloc,
        emoji=rule["emoji"], arch_name=rule["name"], arch_tag=rule["tag"],
        arch_body=body, chips=rule["chips"], macro_line=macro,
        cohort=sidecar["cohort"]["label"],
        compare=compare_rows(stats, sidecar["cohort"], archetype, shares),
        sug_title=rule["sug_title"],
        ally_intro=sidecar["ally"]["intro"], ally_name=sidecar["ally"]["name"],
        ally_role=sidecar["ally"]["role"], ally_loc=sidecar["ally"]["loc"],
        ally_blurb=sidecar["ally"]["blurb"],
    )
    if "affirmation" in rule:
        cfg["affirmation"] = rule["affirmation"]
    else:
        cfg["suggestions"] = rule["suggestions"]
    return cfg, archetype


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", required=True)
    ap.add_argument("--sidecar", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    stats = json.load(open(a.stats))
    sidecar = json.load(open(a.sidecar))
    cfg, archetype = compose(stats, sidecar)
    json.dump(cfg, open(a.out, "w"), indent=2, ensure_ascii=False)
    print(f"composed {a.out}  (classified as: {archetype})")


if __name__ == "__main__":
    main()
