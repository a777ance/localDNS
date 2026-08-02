# Deploy Queue — staging area for the live t630

Everything that has been **reconstructed or fixed in this repo but not yet applied
to the live box** is staged here, in dependency order, as a copy-paste runbook.
The moment SSH access to `192.168.1.118` is available, work this list top-to-bottom
*by stage number* and check items off.

> **The live t630 is the source of truth.** Several stages deploy config that was
> *reconstructed from documentation*, not read off the box. For those, **diff
> against the live file first** (`diff` command given per stage) and reconcile any
> difference into the repo before applying — don't blindly overwrite a working box.

---

## How to read this list

- **Execute in STAGE-NUMBER order — Stage 0 first, Stage 12 last.** Per house
  style the blocks are presented newest-first (Stage 12 at the top, Stage 0 at the
  bottom), but the **numbers are authoritative**: they encode the true dependency
  order. Follow the numbers, not the page order.
- **Legend:**
  - 🆕 **reconstructed** — rebuilt from docs this session; **diff vs live first**.
  - 🐛 **fix** — corrects a real bug; restores documented behavior.
  - ✅ **verify-only** — nothing to deploy; confirm the live box matches.
  - ⛏ **snapshot-back** — pull FROM the box INTO the repo (reverse direction).
- Every "deploy" path maps repo → system per the CLAUDE.md § C deploy table; every
  "verify" mirrors CLAUDE.md § 2.

## Contents (reverse-block order)

- [Stage 12 — Snapshot-back: pull what only lives on the box](#stage-12--snapshot-back-pull-what-only-lives-on-the-box)
- [Stage 11 — Full verification pass](#stage-11--full-verification-pass)
- [Stage 10 — nftables volume layer (per-category accounting)](#stage-10--nftables-volume-layer-per-category-accounting)
- [Stage 9 — Performance + monitoring](#stage-9--performance--monitoring)
- [Stage 8 — AI orchestration (LiteLLM + Open WebUI)](#stage-8--ai-orchestration-litellm--open-webui)
- [Stage 7 — Console (high-seat launcher + ttyd terminals)](#stage-7--console-high-seat-launcher--ttyd-terminals)
- [Stage 6 — WireGuard reconcile](#stage-6--wireguard-reconcile)
- [Stage 5 — Firewall (gates the new ports)](#stage-5--firewall-gates-the-new-ports)
- [Stage 4 — Pi-hole v6](#stage-4--pi-hole-v6)
- [Stage 3 — Unbound drop-ins](#stage-3--unbound-drop-ins)
- [Stage 2 — Host resolver + free :53](#stage-2--host-resolver--free-53)
- [Stage 1 — Secrets (sops + age vault)](#stage-1--secrets-sops--age-vault)
- [Stage 0 — Preconditions + get the code onto the box](#stage-0--preconditions--get-the-code-onto-the-box)

---

## Stage 12 — Snapshot-back: pull what only lives on the box

⛏ These are the repo's remaining gaps that can only be filled *from* the live box —
the opposite direction from every stage below. Do this once the box is reachable so
the repo becomes a complete rollback target.

- [ ] **Odin supervisor** → snapshot `04-user-services/ai-orchestration/langgraph-router/`
  (the LangGraph graph, `odin` CLI, `dispatcher.py`, `requirements.txt`, juror/critic
  roster) from wherever it was authored on the box. Do **not** fabricate it from lore.
- [ ] **`ORCHESTRATION-BLUEPRINT.md`** → snapshot alongside it.
- [ ] **Real sealed secrets** → after Stage 1, commit the age-encrypted
  `vault/*.env.sops` so the repo carries the sealed (safe) copies.
- [ ] Once snapshotted, remove these from the CLAUDE.md § C "drift to reconcile"
  table and the `ALLOW_MISSING` set in `tools/check-docs.py`.

## Stage 11 — Full verification pass

✅ Run the whole CLAUDE.md § 2 checklist; everything should be green.

```bash
systemctl status unbound
dig @127.0.0.1 -p 5335 example.com +dnssec            # 'ad' flag = DNSSEC OK
dig @127.0.0.1 -p 5335 netflix.com +short             # DoT forward path resolves
sudo unbound-control lookup netflix.com               # forwarding → 1.1.1.1@853
sudo unbound-control lookup chase.com                 # iterative delegation (private)
dig @127.0.0.1 -p 5335 console.home.lan +short        # 192.168.1.118 (local-records)
docker ps                                             # pihole + uptime-kuma + litellm + open-webui Up
systemctl is-active console ttyd-thinclient ttyd-laptop
sudo wg show                                          # wg0 up, peers listed
sudo ufw status verbose                               # 51820/udp Anywhere; rest LAN/WG
tc qdisc show dev enp1s0                              # cake bandwidth 85Mbit
cat /sys/class/drm/card*/device/power_dpm_force_performance_level   # high
```

- [ ] All checks pass. Update `docs/ai-cto/context.md` "Current state" (flip the
  reconstructed rows from "not deployed" to "Running") and close the matching
  "Open items".

## Stage 10 — nftables volume layer (per-category accounting)

🆕 Follows the CLAUDE.md § F checklist. Unblocks the by-category GB breakdown in the
Statements. Depends on: the box reachable (Stage 0).

```bash
scp -r docs/statements/tools/collect/ USER@192.168.1.118:~/a777ance/collect/
sudo nft -f ~/a777ance/collect/nftables-accounting.nft
sudo nft list table inet a777acct                     # sets + counters exist, all zero
python3 ~/a777ance/collect/populate_sets.py | head    # dry-run (touches nothing)
sudo python3 ~/a777ance/collect/populate_sets.py --apply
sudo nft -j list counters table inet a777acct         # non-zero bytes within minutes
```

- [ ] Add the two cron lines from CLAUDE.md § F (set-refresh every 6h; nightly stats),
  replacing `USER` with the real login.
- [ ] Then: **test the Statement PWA install on iOS and Android** (was blocked on this).

## Stage 9 — Performance + monitoring

✅/🐛 Mostly verify-only; two fixes to confirm took effect.

- [ ] 🐛 **GPU governor** — the unit now uses `tee` (was an ambiguous-redirect risk).
  Deploy + confirm it forces `high`:
  ```bash
  sudo cp 02-performance/gpu-performance/gpu-performance.service /etc/systemd/system/
  sudo systemctl daemon-reload && sudo systemctl restart gpu-performance
  cat /sys/class/drm/card*/device/power_dpm_force_performance_level   # high
  ```
- [ ] 🐛 **CAKE** — the `cake.service` tc `ExecStop` is now fault-tolerant. Redeploy
  the unit + `cake-setup.sh`; `tc qdisc show dev enp1s0` shows `cake … bandwidth 85Mbit`.
- [ ] ✅ **Unbound cache dir** — confirm `/var/lib/unbound/cache/` exists (create it,
  owned by the unbound user, if not — the dump scripts silently no-op without it):
  ```bash
  sudo install -d -o unbound -g unbound /var/lib/unbound/cache
  ```
- [ ] ✅ **Monitors** — `packet-loss-monitor.sh` / `cake-monitor.sh` cron installed and
  the three Uptime Kuma push tokens filled in.

## Stage 8 — AI orchestration (LiteLLM + Open WebUI)

🆕 Depends on: Stage 1 (`~/llm-router/.env`), Stage 3 (`ai.home.lan` record), Stage 5.

```bash
mkdir -p ~/llm-router && cd ~/llm-router
cp <repo>/04-user-services/ai-orchestration/docker-compose.yml .
cp <repo>/04-user-services/ai-orchestration/config.yaml .
# ~/llm-router/.env comes from Stage 1 (unseal), or from .env.example for a dry run.
$EDITOR config.yaml     # PIN the model IDs + the Tailscale GPU host (CHANGE_ME)
docker compose up -d
```

- [ ] Diff first if a live `~/llm-router/` already exists.
- [ ] Verify: `curl -s http://127.0.0.1:4040/v1/models -H "Authorization: Bearer $LITELLM_MASTER_KEY"`
  lists the tiers; `chat.home.lan:3000` loads (first account = admin, from a trusted device).

## Stage 7 — Console (high-seat launcher + ttyd terminals)

🆕 Depends on: Stage 1 (`/etc/a777ance/ttyd.env`), Stage 3 (names), Stage 5 (ports).

```bash
sudo apt install -y ttyd
sudo install -d /opt/console
sudo install -m 644 <repo>/04-user-services/console/index.html /opt/console/index.html
sudo install -m 644 <repo>/04-user-services/console/console.service         /etc/systemd/system/
sudo install -m 644 <repo>/04-user-services/console/ttyd-thinclient.service /etc/systemd/system/
sudo install -m 644 <repo>/04-user-services/console/ttyd-laptop.service     /etc/systemd/system/
# set User= in all three units to the real login; /etc/a777ance/ttyd.env from Stage 1
sudo systemctl daemon-reload && sudo systemctl enable --now console ttyd-thinclient ttyd-laptop
```

- [ ] Set the real `LAPTOP_SSH` (stable WG/DHCP-reserved IP) in `ttyd.env`.
- [ ] Verify: `systemctl is-active console ttyd-thinclient ttyd-laptop` → three `active`;
  `console.home.lan:8088` loads on the LAN.
- [ ] ⚠️ **Never** port-forward 8088/7681/7682 — LAN + WG only.

## Stage 6 — WireGuard reconcile

✅ The repo `wg0.conf` carries placeholder keys only — the live box holds the real ones.
No overwrite; reconcile instead.

- [ ] ✅ Confirm the live `wg0.conf` has no empty `[Peer]` block (the repo fix commented
  the laptop header) and that MSS clamping is actually traversed under UFW.
- [ ] **Identify or remove peers 10.8.0.4 / .5 / .6** (real keys on the box, no recent
  handshake). Once identified, mirror them into the repo as commented placeholders.
- [ ] **Rotate the Windows laptop key (10.8.0.3)** — exposed during setup. Regenerate on
  the laptop, re-add via the derive-on-server method in `peer-template.conf`.

## Stage 5 — Firewall (gates the new ports)

🐛 `ufw/setup.sh` now gates the console + router ports (8088/7681/7682/4040/3000). Re-run
it so those services are actually reachable (LAN + WG) — and nothing else is.

```bash
sudo bash <repo>/01-core-network/ufw/setup.sh
sudo ufw status verbose      # 51820/udp Anywhere; everything else LAN/WG only
```

- [ ] Confirm 8088/7681/7682/4040/3000 appear for `192.168.0.0/16` and `10.8.0.0/24` only.

## Stage 4 — Pi-hole v6

🆕/🐛 The compose was migrated to v6 `FTLCONF_*` vars (v5 vars were silently ignored).
Depends on: Stage 1 (`~/pihole/.env`), Stage 2 (`:53` freed), Stage 3 (Unbound up).

```bash
cd ~/pihole
diff docker-compose.yml <repo>/01-core-network/pihole/docker-compose.yml   # reconcile first
cp <repo>/01-core-network/pihole/docker-compose.yml .
# ~/pihole/.env (PIHOLE_WEBPASSWORD) comes from Stage 1
docker compose up -d
```

- [ ] Verify Settings → DNS shows the single upstream `127.0.0.1#5335`, no presets.
- [ ] Confirm the v6 `FTLCONF_webserver_port` syntax actually binds 8080 (flagged in the
  compose comment); adjust if the box wants `"8080,443s"`-style.

## Stage 3 — Unbound drop-ins

🆕 Deploy the new `local-records.conf` (LAN names) and verify the other five drop-ins
match the box. Depends on: Stage 2 (host resolver) not strictly, but do DNS together.

```bash
diff /etc/unbound/unbound.conf.d/local-records.conf \
     <repo>/01-core-network/unbound/local-records.conf 2>/dev/null   # may not exist yet
sudo cp <repo>/01-core-network/unbound/local-records.conf /etc/unbound/unbound.conf.d/
sudo systemctl restart unbound
```

- [ ] **Verify each `local-data` line matches the live box** (names/IP/`transparent` were
  reconstructed). `dig @127.0.0.1 -p 5335 chat.home.lan +short` → `192.168.1.118`.
- [ ] ✅ Diff the other five drop-ins (`server`, `tuning`, `streaming-forward`,
  `remote-control`, `root-auto-trust-anchor-file`) against the box; reconcile any drift.

## Stage 2 — Host resolver + free :53

🐛 **Functional fix.** `host-dns.conf` now includes `DNSStubListener=no` (was missing) so
host-net Pi-hole can bind `0.0.0.0:53`. Apply this **before** Stage 4.

```bash
diff /etc/systemd/resolved.conf.d/host-dns.conf \
     <repo>/01-core-network/host-dns/host-dns.conf
sudo cp <repo>/01-core-network/host-dns/host-dns.conf /etc/systemd/resolved.conf.d/
sudo systemctl restart systemd-resolved
sudo ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf     # off the stub
```

- [ ] Verify `:53` is free before starting Pi-hole: `sudo ss -ulpn 'sport = :53'` (empty).
- [ ] Verify host resolution: `getent hosts security.ubuntu.com` returns an IP.

## Stage 1 — Secrets (sops + age vault)

🆕 Stand up the vault so every downstream `.env` exists. The tooling is in `vault/`; the
sealed `*.env.sops` do **not** exist yet — create them from the real values on the box.

```bash
age-keygen -o ~/.config/sops/age/keys.txt          # keep the private key OFF the repo
# put the age PUBLIC key into vault/.sops.yaml (replace CHANGE_ME)
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
mkdir -p vault/cleartext
# write real values into vault/cleartext/{pihole,llm-router,ttyd,jury,jury-claude}.env
cd vault && ./seal.sh && ./unseal.sh               # seal → commit; unseal → deploy paths
```

- [ ] `unseal.sh` writes each secret to its `secrets.manifest` path (chmod 600):
  `~/pihole/.env`, `~/llm-router/.env`, `/etc/a777ance/ttyd.env`, the two Jury `.env`s.
- [ ] Commit the sealed `vault/*.env.sops` (age-encrypted, safe) — that's the Stage 12 ⛏.
- [ ] *(Deferred, per the flagged gap)* the `wg-peer` / `all` / `apps` rotation subcommands
  and a sealed WireGuard **server** key are not built yet — see `vault/README.md`.

## Stage 0 — Preconditions + get the code onto the box

Everything below assumes these hold.

```bash
ssh USER@192.168.1.118          # or ssh USER@10.8.0.1 over WireGuard
# On the box, get this branch's files. Either clone/pull the repo:
git clone <repo-url> ~/localDNS && cd ~/localDNS && git checkout claude/new-session-nb82mn
# …or scp individual files (paths are given per stage as <repo>/…).
```

- [ ] SSH + `sudo` confirmed.
- [ ] This branch checked out on the box (or files stated per stage are reachable).
- [ ] `python3 tools/check-docs.py` green before you start (sanity: repo is consistent).
