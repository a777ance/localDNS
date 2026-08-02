# Console — the High Seat

> **Reconstructed from documentation, not yet verified against the live box.**
> These files are rebuilt from the CLAUDE.md topology table, the Known-issues
> entries, and `docs/ai-cto/context.md` (Step 13). The live t630 at
> `192.168.1.118` remains the source of truth — confirm ports, unit contents, and
> the `User=` / SSH-jump target on the box before trusting this as a rollback
> target. Ship-blocking values (`ttyd` credential, laptop SSH address) are
> `CHANGE_ME` placeholders here and must never be committed with real values.

A tiny host-side launcher that pins every service on the t630 behind a stable
name, plus two `ttyd` web terminals. Everything is **LAN + WireGuard only** —
never port-forward `8088`/`7681`/`7682` to the internet. Remote access is through
the WireGuard tunnel (Step 7), full stop.

## What runs

| Piece | Unit | Port | Serves |
| ----- | ---- | ---- | ------ |
| High-seat launcher | `console.service` | 8088 | Static `index.html` — one card per realm |
| Web terminal (thin client) | `ttyd-thinclient.service` | 7681 | A login shell **on the t630** |
| Web terminal (laptop) | `ttyd-laptop.service` | 7682 | SSH jump from the t630 to the laptop |

Names come from `01-core-network/unbound/local-records.conf`:
`console.home.lan:8088`, `term.home.lan:7681`, `laptop.home.lan:7682` (plus
`ai`/`chat`/`kuma`/`pihole` for the launcher cards).

## Deploy

```bash
sudo apt install -y ttyd                       # thin client + laptop terminals
sudo install -d /opt/console
sudo install -m 644 index.html /opt/console/index.html

# Credentials + laptop target — never in git. chmod 600, root-owned.
sudo install -d /etc/a777ance
sudo install -m 600 ttyd.env.example /etc/a777ance/ttyd.env
sudo editor /etc/a777ance/ttyd.env             # set TTYD_CREDENTIAL and LAPTOP_SSH

# Set User= in each unit to the real login on the box, then:
sudo install -m 644 console.service          /etc/systemd/system/console.service
sudo install -m 644 ttyd-thinclient.service  /etc/systemd/system/ttyd-thinclient.service
sudo install -m 644 ttyd-laptop.service      /etc/systemd/system/ttyd-laptop.service
sudo systemctl daemon-reload
sudo systemctl enable --now console ttyd-thinclient ttyd-laptop

# Re-run the firewall so 8088/7681/7682 are gated to LAN + WG only.
sudo bash ../../01-core-network/ufw/setup.sh
```

Verify: `systemctl is-active console ttyd-thinclient ttyd-laptop` → three
`active`, and `dig @127.0.0.1 -p 5335 console.home.lan +short` → `192.168.1.118`.

## Security — read before exposing anything

- **The `ttyd --credential` is the only gate to a root-capable shell.** Treat it
  like a root password. It lives in `/etc/a777ance/ttyd.env` (`chmod 600`), never
  in git. Rotate it out of the sops+age vault, not by hand.
- **LAN + WG only.** UFW scopes `8088`/`7681`/`7682` to `192.168.0.0/16` and
  `10.8.0.0/24`. Do not add an `Anywhere` rule and do not port-forward on the
  Netgear. A web terminal on the public internet is a remote root shell.
- **Hardening still to do** (notes, not yet applied on the box):
  - **TLS:** run `ttyd -S` with a cert so the shell isn't plaintext HTTP over the
    LAN. Needs a cert/key path in the unit.
  - **`login` over `bash`:** the units below run `login` (which prompts for an OS
    account) rather than dropping straight into `bash` as the service user, so a
    leaked `ttyd` credential still hits the OS auth wall.
- **Laptop target must be stable.** `LAPTOP_SSH` points at the laptop's WireGuard
  IP or a DHCP-reserved LAN IP — never a floating lease, or the laptop terminal
  breaks when the lease rotates.

## Browser-as-Odin

`browser-odin.md` documents the sidebar / session-persistence setup that turns a
kiosk browser pointed at `console.home.lan:8088` into the always-on "high seat."
