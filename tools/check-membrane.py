#!/usr/bin/env python3
"""Enforce the membrane invariants structurally, instead of by memory.

Four invariants live in CLAUDE.md as prose. Prose is enforced by whoever
remembers to read it. This script enforces them mechanically, so a violation
fails a commit instead of surviving until someone notices.

Each check is named for the cell-biology finding that produced it
(docs/architecture/microbiology/) — not decoration: the biology is what says
*why* the rule is load-bearing rather than fastidious, and the entry for each
carries the reasoning and the disanalogy.

  1. AQUAPORIN      A channel built for bulk throughput must not also carry the
                    sensitive thing. Aquaporin passes water and blocks protons,
                    because a proton leak would short out the very gradient the
                    membrane is maintained to hold — and it would do it at the
                    channel's own optimized rate. So: no sensitive domain may
                    appear as a forward-zone, and every forward-zone must be
                    encrypted (this path once fanned out over plaintext UDP/53).

  2. LEAFLET        The two faces of a bilayer are chemically different, kept so
                    at continuous cost. An inner-leaflet fact appearing on the
                    outer face is itself the alarm (phosphatidylserine exposure).
                    So: LAN-only names and private addresses must not appear on
                    any published, customer-facing surface.

  3. FUSION         A liposome made of membrane merges instead of crossing —
                    admission by resemblance, inspected by nothing. Every
                    `network_mode: host` container is one. They are all
                    justified; the risk is that the *count* drifts upward
                    unnoticed. So: the register in CLAUDE.md must match reality.

  4. CMC            Every amphiphile dissolves the membrane above its critical
                    micelle concentration. Tunnels are amphiphiles. So: every
                    active WireGuard peer must be named, and the count must stay
                    within the declared budget. An unnamed peer counts toward CMC
                    and buys nothing.

Standard library only. Exits non-zero on any violation so it can gate a commit
or a CI run.

Usage:
    python3 tools/check-membrane.py
    python3 tools/check-membrane.py -v      # also print what passed, in detail
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORWARD_CONF = "01-core-network/unbound/streaming-forward.conf"
LOCAL_RECORDS = "01-core-network/unbound/local-records.conf"
WG_CONF = "01-core-network/wireguard/wg0.conf"
BRIEFING = "CLAUDE.md"

# Surfaces that face the outer leaflet: published to the world, or handed to a
# customer. Deploy tooling is excluded — an nftables ruleset legitimately names
# the private ranges it scopes.
PUBLISHED_GLOBS = ("docs/statements",)
PUBLISHED_SUFFIXES = (".html", ".json")
PUBLISHED_EXCLUDE = ("docs/statements/tools/collect",)

# --- Check 1 data -----------------------------------------------------------

# Substrings that mark a domain as sensitive. Deliberately blunt: a false
# positive here costs one conversation, a false negative hands Cloudflare a
# private lookup. Keep it that way.
SENSITIVE_SUBSTRINGS = (
    # finance
    "bank", "chase", "wellsfargo", "citi", "capitalone", "usbank", "pnc",
    "schwab", "fidelity", "vanguard", "coinbase", "paypal", "venmo", "stripe",
    "intuit", "turbotax", "quickbooks", "creditkarma", "equifax", "experian",
    "transunion",
    # health
    "health", "medical", "clinic", "hospital", "pharma", "cvs", "walgreens",
    "mychart", "epic.com", "kaiser", "anthem", "cigna", "aetna", "unitedhealth",
    "labcorp", "questdiagnostics", "goodrx", "psych", "therapy", "rehab",
    # government / legal / identity
    ".gov", "irs", "ssa", "medicare", "medicaid", "uscis", "dmv", "courts",
    "legal", "lawyer", "attorney",
    # personal comms & identity
    "mail.", "gmail", "outlook", "proton", "tutanota", "fastmail", "zoho",
    "signal", "whatsapp", "telegram", "messenger",
    # faith, family, dating, employment — sensitive by inference, not content
    "church", "parish", "diocese", "adoption", "fertility", "planned",
    "dating", "match.com", "indeed", "linkedin", "glassdoor",
    # our own interior
    "home.lan", "a777ance",
)

# --- Check 4 data -----------------------------------------------------------

# The declared amphiphile budget. Raising this number is a deliberate act and
# should be argued for (see docs/architecture/microbiology/amphiphiles.md §5),
# not a side effect of adding a device.
WG_PEER_BUDGET = 4

failures = []
notes = []


def read(rel):
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        failures.append(f"{rel}: missing — cannot verify the invariants it carries")
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def fail(check, msg):
    failures.append(f"[{check}] {msg}")


def note(check, msg):
    notes.append(f"[{check}] {msg}")


# ---------------------------------------------------------------------------
# 1. AQUAPORIN — the fast channel carries bulk, never the credential.
# ---------------------------------------------------------------------------
def check_aquaporin():
    text = read(FORWARD_CONF)
    if text is None:
        return

    # Parse forward-zone blocks: a `name:` plus the directives that follow it,
    # up to the next block. Commented lines are not live config.
    live = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    blocks, current = [], None
    for ln in live:
        if ln.strip().startswith("forward-zone:"):
            current = {"name": None, "tls": False, "addrs": []}
            blocks.append(current)
        elif current is not None:
            m = re.match(r'\s*name:\s*"?([^"\s]+)"?', ln)
            if m:
                current["name"] = m.group(1).rstrip(".").lower()
            if re.match(r"\s*forward-tls-upstream:\s*yes", ln):
                current["tls"] = True
            m = re.match(r"\s*forward-addr:\s*(\S+)", ln)
            if m:
                current["addrs"].append(m.group(1))
            if ln.strip().startswith("server:"):
                current = None

    if not blocks:
        fail("AQUAPORIN", f"{FORWARD_CONF}: no forward-zone blocks parsed — "
                          "either the file changed shape or the parser is wrong; "
                          "both mean this check is not actually running")
        return

    for b in blocks:
        name = b["name"]
        if not name:
            fail("AQUAPORIN", "a forward-zone block has no name:")
            continue

        # 1a. Proton exclusion: nothing sensitive on the fast path.
        for bad in SENSITIVE_SUBSTRINGS:
            if bad in name:
                fail("AQUAPORIN",
                     f'forward-zone "{name}" matches sensitive marker "{bad}". '
                     "The forward-path hands these lookups to Cloudflare. A fast "
                     "channel that carries the sensitive thing does not leak a "
                     "little — it shorts the gradient at the channel's own rate. "
                     "Remove it, or resolve it recursively (the default).")

        # 1b. The channel is encrypted. This path once fanned out over plaintext
        #     UDP/53 to ~18 resolvers, leaking every streaming lookup to the ISP.
        if not b["tls"]:
            fail("AQUAPORIN",
                 f'forward-zone "{name}" has no `forward-tls-upstream: yes` — '
                 "that is the plaintext regression this design was built to end.")

        for addr in b["addrs"]:
            if "@853" not in addr:
                fail("AQUAPORIN",
                     f'forward-zone "{name}": forward-addr {addr} is not on :853 '
                     "(DoT). Port 53 here is cleartext to the ISP.")
            if "#" not in addr:
                fail("AQUAPORIN",
                     f'forward-zone "{name}": forward-addr {addr} has no '
                     "#hostname suffix, so the upstream certificate is not "
                     "validated against a name — encrypted to nobody in particular.")

    note("AQUAPORIN",
         f"{len(blocks)} forward-zones, all DoT-on-853 with cert names, "
         "none matching a sensitivity marker")


# ---------------------------------------------------------------------------
# 2. LEAFLET — an inner-face fact must not appear on the outer face.
# ---------------------------------------------------------------------------
def published_files():
    for top in PUBLISHED_GLOBS:
        for dirpath, _, filenames in os.walk(os.path.join(REPO, top)):
            rel_dir = os.path.relpath(dirpath, REPO)
            if any(rel_dir.startswith(x) for x in PUBLISHED_EXCLUDE):
                continue
            for fn in filenames:
                if fn.endswith(PUBLISHED_SUFFIXES):
                    yield os.path.relpath(os.path.join(dirpath, fn), REPO)


def check_leaflet():
    records = read(LOCAL_RECORDS)
    if records is None:
        return

    names, addrs = set(), set()
    for ln in records.splitlines():
        if ln.lstrip().startswith("#"):
            continue
        m = re.search(r'local-data:\s*"(\S+)\.\s+IN\s+A\s+(\S+)"', ln)
        if m:
            names.add(m.group(1).lower())
            addrs.add(m.group(2))

    if not names:
        fail("LEAFLET", f"{LOCAL_RECORDS}: no local-data names parsed — "
                        "this check would silently pass on anything")
        return

    # The interior facts: LAN-only names, the t630's address, the tunnel range.
    interior = {n: f'LAN-only name "{n}"' for n in names}
    for a in addrs:
        interior[a] = f"the t630's private address {a}"
    interior["10.8.0."] = "the WireGuard tunnel range 10.8.0.0/24"

    checked = 0
    for rel in published_files():
        checked += 1
        with open(os.path.join(REPO, rel), encoding="utf-8", errors="replace") as fh:
            body = fh.read().lower()
        for needle, desc in interior.items():
            if needle.lower() in body:
                fail("LEAFLET",
                     f"{rel} carries {desc}. That is an inner-leaflet fact on the "
                     "outer face — the published, customer-facing surface. Nothing "
                     "benign puts it there.")

    # The fast path is an outer-face channel too: a LAN-only name must never be
    # forwarded to a public resolver.
    fwd = read(FORWARD_CONF)
    if fwd:
        live = "\n".join(ln for ln in fwd.splitlines()
                         if not ln.lstrip().startswith("#")).lower()
        for n in names:
            if n in live:
                fail("LEAFLET",
                     f'LAN-only name "{n}" appears in {FORWARD_CONF} — it would '
                     "be published to Cloudflare. These names resolve only on the "
                     "LAN/VPN and must never reach a public resolver.")

    note("LEAFLET",
         f"{len(names)} LAN-only names + {len(addrs)} private address(es) absent "
         f"from {checked} published files and from the forward-path")


# ---------------------------------------------------------------------------
# 3. FUSION — the host-network register must match reality.
# ---------------------------------------------------------------------------
def check_fusion():
    actual = {}
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if not fn.endswith((".yml", ".yaml")):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), REPO)
            with open(os.path.join(dirpath, fn), encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            service = None
            for ln in lines:
                m = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", ln)
                if m:
                    service = m.group(1)
                if re.match(r"\s*network_mode:\s*host\s*$", ln) and service:
                    actual[service.lower()] = rel

    briefing = read(BRIEFING)
    if briefing is None:
        return

    m = re.search(r"<!-- fusion-register:start -->(.*?)<!-- fusion-register:end -->",
                  briefing, re.S)
    if not m:
        fail("FUSION",
             f"{BRIEFING} has no fusion register (the "
             "<!-- fusion-register:start/end --> block). Every `network_mode: host` "
             "container runs *as* the membrane rather than behind it; the register "
             "is what makes going from N to N+1 a visible event.")
        return

    registered = set(re.findall(r"^\|\s*`([^`]+)`\s*\|", m.group(1), re.M))
    registered = {r.lower() for r in registered}
    have = set(actual)

    for svc in sorted(have - registered, reverse=True):
        fail("FUSION",
             f"`{svc}` ({actual[svc]}) runs network_mode: host but is not in the "
             f"fusion register in {BRIEFING}. It fused with the membrane without "
             "being counted — add it with its justification, or give it a network.")
    for svc in sorted(registered - have, reverse=True):
        fail("FUSION",
             f"`{svc}` is in the fusion register but no compose file gives it "
             "network_mode: host. Stale entry — a register nobody trusts is worse "
             "than none.")

    if have == registered:
        note("FUSION", f"{len(have)} fused container(s), all registered: "
                       + ", ".join(sorted(have, reverse=True)))


# ---------------------------------------------------------------------------
# 4. CMC — count the amphiphiles; every one of them named.
# ---------------------------------------------------------------------------
def check_cmc():
    text = read(WG_CONF)
    if text is None:
        return

    lines = text.splitlines()
    peers = []
    for i, ln in enumerate(lines):
        if ln.strip() != "[Peer]":       # commented placeholders are not live
            continue
        block, j = [], i + 1
        while j < len(lines):
            # A block ends at the next section header — live *or* commented out.
            # The commented `# [Peer]` placeholders below the live peers are
            # separate blocks; without stripping the comment marker first, a live
            # peer swallows every placeholder that follows it.
            if lines[j].lstrip("# \t").startswith("["):
                break
            block.append(lines[j])
            j += 1
        peers.append("\n".join(block))

    for p in peers:
        ip = re.search(r"AllowedIPs\s*=\s*(\S+)", p)
        label = ip.group(1) if ip else "(no AllowedIPs)"
        comments = [c.strip("# ").strip() for c in p.splitlines()
                    if c.lstrip().startswith("#")]
        named = [c for c in comments if c and "UNIDENTIFIED" not in c.upper()]
        if not named:
            fail("CMC",
                 f"WireGuard peer {label} has no identifying comment. An unnamed "
                 "peer counts toward the critical micelle concentration and buys "
                 "nothing — identify the device or remove the peer.")
        if any("UNIDENTIFIED" in c.upper() for c in comments):
            fail("CMC",
                 f"WireGuard peer {label} is marked UNIDENTIFIED while live. "
                 "Identify it or remove it.")

    if len(peers) > WG_PEER_BUDGET:
        fail("CMC",
             f"{len(peers)} live WireGuard peers exceeds the declared budget of "
             f"{WG_PEER_BUDGET}. Raising the budget is a deliberate act — argue "
             "for it in the commit, do not bump the constant in passing.")

    note("CMC", f"{len(peers)} live peer(s) of {WG_PEER_BUDGET} budgeted, all named")


def main():
    verbose = "-v" in sys.argv
    for fn in (check_aquaporin, check_leaflet, check_fusion, check_cmc):
        fn()

    if verbose:
        for n in notes:
            print("ok   " + n)

    if failures:
        print()
        for f in failures:
            print("FAIL " + f)
        print(f"\n{len(failures)} membrane invariant violation(s).")
        return 1

    print(f"All 4 membrane invariants hold "
          f"(aquaporin, leaflet, fusion, CMC) — {len(notes)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
