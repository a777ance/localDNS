#!/usr/bin/env python3
"""
populate_sets.py — fill the nftables accounting IP-sets from categories.json.

This is the missing half of the volume-by-category layer, and the single piece
that turns the Traffic Allocation donut + Household Profile "macros" from sample
data into MEASURED data.

  nftables-accounting.nft  defines the per-category counters AND the IP *sets*,
                           but the sets start EMPTY — nothing is counted until a
                           destination IP is a member of a set.

  categories.json          maps each category to its domains. CDN IPs rotate, so
                           we don't hard-code them.

This job resolves every domain to its current A records and pushes them into the
matching set with a timeout, so stale CDN IPs age out on their own. Run it a few
times a day from cron (see README.md).

  categories.json --resolve--> A records --(add element)--> cat_* sets
                                                  |
                       nftables-accounting.nft counts bytes per set
                                                  |
                       collect_stats.py reads `nft -j list counters`

Safe anywhere: the default just PRINTS the nft commands (a dry run that resolves
real DNS but touches nothing). Use --apply on the box (needs root + the ruleset
loaded) to actually program the sets.

    python3 populate_sets.py                 # dry run, prints the nft script
    sudo python3 populate_sets.py --apply    # on the t630, programs the sets
"""
import argparse, ipaddress, json, os, socket, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# statement category (categories.json key) -> nft set name (nftables-accounting.nft).
# Must stay in sync with both files; "Other" is the catch-all and has no set.
CATEGORY_TO_SET = {
    "Streaming & Video":  "cat_streaming",
    "Social & Messaging": "cat_social",
    "Cloud & Backups":    "cat_cloud",
    "Video Conferencing": "cat_conferencing",
    "Gaming & Downloads": "cat_gaming",
    "Smart Home / IoT":   "cat_iot",
    "Web & SaaS":         "cat_saas",
    "Shopping & Web":     "cat_shopping",
}


def resolve_a(domain):
    """Best-effort: the set of IPv4 addresses currently behind a domain.
    Uses the process-wide socket timeout set in main()."""
    try:
        infos = socket.getaddrinfo(domain, None, family=socket.AF_INET)
    except OSError:
        return set()
    out = set()
    for ai in infos:
        ip = ai[4][0]
        try:
            # Only count public CDN destinations; drop 0.0.0.0, loopback, RFC1918,
            # link-local — a category domain resolving to those is parked/blocked.
            if ipaddress.ip_address(ip).is_global:
                out.add(ip)
        except ValueError:
            pass
    return out


def main():
    ap = argparse.ArgumentParser(description="Populate nftables accounting sets from categories.json")
    ap.add_argument("--categories", default=os.path.join(HERE, "categories.json"))
    ap.add_argument("--table", default="a777acct")
    ap.add_argument("--family", default="inet")
    ap.add_argument("--timeout", default="24h", help="nft element timeout; stale CDN IPs age out")
    ap.add_argument("--apply", action="store_true", help="run nft (needs root); default only prints")
    ap.add_argument("--verbose", action="store_true", help="log every domain -> IPs to stderr")
    a = ap.parse_args()

    socket.setdefaulttimeout(3.0)
    cats = json.load(open(a.categories))["categories"]

    commands, total_ips = [], 0
    for category, domains in cats.items():
        setname = CATEGORY_TO_SET.get(category)
        if not setname:
            print(f"[warn] no nft set mapped for category '{category}' — skipping", file=sys.stderr)
            continue
        ips = set()
        for d in domains:
            got = resolve_a(d)
            if a.verbose:
                print(f"  {setname}: {d} -> {sorted(got) or '(none)'}", file=sys.stderr)
            ips |= got
        if not ips:
            continue
        total_ips += len(ips)
        elements = ", ".join(f"{ip} timeout {a.timeout}" for ip in sorted(ips))
        commands.append(f"add element {a.family} {a.table} {setname} {{ {elements} }}")

    if not commands:
        print("[warn] resolved no IPs (no network, or empty categories.json)", file=sys.stderr)
        return 1

    if a.apply:
        script = "\n".join(commands) + "\n"
        proc = subprocess.run(["nft", "-f", "-"], input=script, text=True)
        if proc.returncode != 0:
            print("[error] nft failed — is the ruleset loaded "
                  "(`sudo nft -f nftables-accounting.nft`) and are you root?", file=sys.stderr)
            return proc.returncode
        print(f"applied: {len(commands)} sets, {total_ips} IPs", file=sys.stderr)
    else:
        print("\n".join(commands))
        print(f"# dry run: {len(commands)} sets, {total_ips} IPs. "
              f"Re-run with --apply on the box to program them.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
