#!/usr/bin/env python3
"""
collect_stats.py — gather one home's MEASURED figures on the t630.

Outputs a stats.json with only what the appliance can actually prove:
  - queries / blocks / protection rate     (Pi-hole FTL long-term DB)
  - uptime / peak latency                  (Uptime Kuma Prometheus metrics)
  - VPN sessions                           (wg show)
  - per-category volume in bytes           (nftables counters, see nftables-accounting.nft)
  - device count                           (distinct clients in the FTL DB)

It deliberately does NOT write narrative copy (profile prose, suggestions,
"Handled For You"). That is added by compose.py + the operator's change log.

Run on the box:
  python3 collect_stats.py --out /tmp/A77-001.stats.json \
      --ftl-db /etc/pihole/pihole-FTL.db --kuma-metrics http://127.0.0.1:3001/metrics \
      --kuma-key "$KUMA_API_KEY" --wg-iface wg0

Test anywhere (no box needed):
  python3 collect_stats.py --sample --out /tmp/sample.stats.json
"""
import argparse, json, subprocess, sqlite3, time, calendar, datetime as dt, urllib.request, re, sys

# Pi-hole FTL query.status values that mean "blocked"
BLOCKED_STATUSES = (1, 4, 5, 9, 10, 11)

# nft counter name -> statement category bucket
NFT_TO_CATEGORY = {
    "c_streaming": "Streaming & Video", "c_social": "Social & Messaging",
    "c_cloud": "Cloud & Backups", "c_conferencing": "Video Conferencing",
    "c_gaming": "Gaming & Downloads", "c_iot": "Smart Home / IoT",
    "c_saas": "Web & SaaS", "c_shopping": "Shopping & Web", "c_other": "Other",
}


def month_bounds(year, month):
    start = int(dt.datetime(year, month, 1).timestamp())
    last = calendar.monthrange(year, month)[1]
    end = int(dt.datetime(year, month, last, 23, 59, 59).timestamp())
    return start, end


def pihole_stats(db_path, start, end):
    """Totals + distinct device count from the FTL long-term DB."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM queries WHERE timestamp BETWEEN ? AND ?", (start, end))
    total = cur.fetchone()[0]
    q = "SELECT COUNT(*) FROM queries WHERE timestamp BETWEEN ? AND ? AND status IN (%s)" % \
        ",".join("?" * len(BLOCKED_STATUSES))
    cur.execute(q, (start, end, *BLOCKED_STATUSES))
    blocked = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT client) FROM queries WHERE timestamp BETWEEN ? AND ?", (start, end))
    devices = cur.fetchone()[0]
    con.close()
    return total, blocked, devices


def kuma_metrics(url, api_key, monitor_names):
    """Parse Uptime Kuma's Prometheus /metrics for uptime% and avg response time.
    Kuma exposes monitor_status (1=up) and monitor_response_time per monitor."""
    req = urllib.request.Request(url)
    if api_key:
        import base64
        token = base64.b64encode(f":{api_key}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    body = urllib.request.urlopen(req, timeout=10).read().decode()
    up, rt = [], []
    for line in body.splitlines():
        if line.startswith("monitor_status") and any(n in line for n in monitor_names):
            up.append(float(line.rsplit(" ", 1)[1]))
        if line.startswith("monitor_response_time") and any(n in line for n in monitor_names):
            rt.append(float(line.rsplit(" ", 1)[1]))
    uptime_pct = round(100.0 * sum(up) / len(up), 2) if up else None
    peak_latency = round(max(rt)) if rt else None
    return uptime_pct, peak_latency


def wg_sessions(iface):
    """Peers with a handshake in the last 3 minutes ~= active sessions this period.
    (For a monthly count, sum unique peers seen across periodic samples instead.)"""
    out = subprocess.check_output(["wg", "show", iface, "dump"], text=True)
    now = int(time.time())
    sessions = 0
    for line in out.splitlines()[1:]:          # first line is the interface itself
        cols = line.split("\t")
        if len(cols) >= 5 and cols[4].isdigit():
            if cols[4] != "0" and now - int(cols[4]) < 180:
                sessions += 1
    return sessions


def nft_category_bytes(table="a777acct"):
    """Read per-category byte counters from the nftables accounting table."""
    out = subprocess.check_output(["nft", "-j", "list", "counters", "table", "inet", table], text=True)
    data = json.loads(out)
    by_cat = {}
    for obj in data.get("nftables", []):
        c = obj.get("counter")
        if c and c.get("name") in NFT_TO_CATEGORY:
            by_cat[NFT_TO_CATEGORY[c["name"]]] = int(c.get("bytes", 0))
    return by_cat


def sample():
    GB = 1024 ** 3
    return {
        "collected_at": dt.datetime.now().isoformat(timespec="seconds"),
        "queries": {"total": 52441, "blocked": 9847},
        "uptime": {"pct": 99.9, "downtime_min": 8},
        "latency_ms": {"peak": 12},
        "vpn_sessions": {"count": 14},
        "devices": 5,
        "volume": {"by_category": {
            "Streaming & Video": int(199.7 * GB), "Social & Messaging": int(87.7 * GB),
            "Cloud & Backups": int(68.2 * GB), "Gaming & Downloads": int(53.6 * GB),
            "Smart Home / IoT": int(39.0 * GB), "Shopping & Web": int(24.4 * GB),
            "Other": int(14.4 * GB)}},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample", action="store_true", help="emit synthetic stats (no box needed)")
    ap.add_argument("--ftl-db", default="/etc/pihole/pihole-FTL.db")
    ap.add_argument("--kuma-metrics", default="http://127.0.0.1:3001/metrics")
    ap.add_argument("--kuma-key", default="")
    ap.add_argument("--kuma-monitors", default="DNS,Unbound,WAN")
    ap.add_argument("--wg-iface", default="wg0")
    ap.add_argument("--year", type=int, default=dt.date.today().year)
    ap.add_argument("--month", type=int, default=dt.date.today().month)
    a = ap.parse_args()

    if a.sample:
        stats = sample()
    else:
        start, end = month_bounds(a.year, a.month)
        stats = {"collected_at": dt.datetime.now().isoformat(timespec="seconds")}
        # Each source is best-effort: a missing source leaves its field null rather than
        # aborting the whole run, so a statement can still be produced from what we have.
        try:
            total, blocked, devices = pihole_stats(a.ftl_db, start, end)
            stats["queries"] = {"total": total, "blocked": blocked}
            stats["devices"] = devices
        except Exception as e:
            print(f"[warn] pihole: {e}", file=sys.stderr); stats["queries"] = None
        try:
            up, lat = kuma_metrics(a.kuma_metrics, a.kuma_key, a.kuma_monitors.split(","))
            stats["uptime"] = {"pct": up}; stats["latency_ms"] = {"peak": lat}
        except Exception as e:
            print(f"[warn] kuma: {e}", file=sys.stderr); stats["uptime"] = None
        try:
            stats["vpn_sessions"] = {"count": wg_sessions(a.wg_iface)}
        except Exception as e:
            print(f"[warn] wg: {e}", file=sys.stderr); stats["vpn_sessions"] = None
        try:
            stats["volume"] = {"by_category": nft_category_bytes()}
        except Exception as e:
            print(f"[warn] nft: {e}", file=sys.stderr); stats["volume"] = None

    with open(a.out, "w") as f:
        json.dump(stats, f, indent=2)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
