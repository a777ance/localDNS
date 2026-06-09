# 11 · Console — Hliðskjálf, the high seat

> Briefing: [`../CLAUDE.md`](../CLAUDE.md) · Full guide: [`../README.md`](../README.md) (this is **Step 13**) ·
> The browser half: [`browser-odin.md`](browser-odin.md)

One place to reach everything on the t630 — the AI front door, a shell on each
Linux box, and the watch posts — each by name, gated to the LAN and the WireGuard
tunnel. **Odin's high seat sees into every realm; this page is the view from it.**
The browser you pin it in *is* the operator's Odin (the human twin of the machine
Odin in [`10-ai-orchestration/`](../10-ai-orchestration/)); see
[`browser-odin.md`](browser-odin.md) for that half.

This stage adds **no new daemons you have to babysit** — a static page and two
`ttyd` terminals, all host-side systemd units, all behind the one UFW choke point.

---

## The realms

| Realm | Name (pin this) | Port | What it is |
| ----- | --------------- | ---- | ---------- |
| Open WebUI | `chat.home.lan` | 3000 | The AI chat UI (fronts the router) |
| LiteLLM router | `ai.home.lan` | 4040 | The AI front door / API |
| Thin client shell | `term.home.lan` | 7681 | `ttyd` login shell on the t630 |
| Laptop shell | `laptop.home.lan` | 7682 | `ttyd` → SSH to the laptop (t630 jumps) |
| Pi-hole | `pihole.home.lan` | 8080 | DNS &amp; ad-blocking admin |
| Uptime Kuma | `kuma.home.lan` | 3001 | Service / uptime monitoring |
| **The high seat** | **`console.home.lan`** | **8088** | **This launcher — the map to all of the above** |

All seven names resolve to `192.168.1.118` via
[`../01-unbound/local-records.conf`](../01-unbound/local-records.conf). The two
terminals are *served by the t630* — `laptop.home.lan` is the t630 port that SSHes
onward to the laptop, which is why its name points at the t630, not the laptop.

---

## ⚠️ Security — read before you expose a shell

A web terminal is a **login to the box over HTTP**. Anyone who reaches the port and
knows the `ttyd` credential gets a shell as that user (usually `sudo`-capable). So:

- **LAN + WireGuard only — never the internet.** UFW gates 8088/7681/7682 to
  `192.168.0.0/16` + `10.8.0.0/24`. Do not port-forward these on the router. Remote
  access is *through WireGuard*, never a public port.
- **The `ttyd` credential is a root password.** Long, unique, in
  `/etc/a777ance/ttyd.env` (`chmod 600`), never in git. Rotate it like one.
- **The laptop stays off the wire.** The t630 is the jump host; the laptop only
  needs `sshd` and never exposes a web port of its own. SSH auth is interactive
  (the page prompts for the laptop password) unless you opt into a key (Step 3).
- **Harden further when you can:** add TLS so the credential isn't sent in the clear
  even on the LAN — `ttyd -S --ssl-cert … --ssl-key …` (self-signed is fine for a
  homelab); and swap `bash -l` for `login` to force an OS credential on top of
  ttyd's. Both are noted inline in the unit files.

---

## Deploy

Run on the t630. **Blocks are listed last-first (house style); the step numbers are
the execution order — follow them low→high.** All of it is one SSH session.

### Block C — wire it in (DNS + firewall)

**Step 5.** Add the seven names (already in the repo file) and reload Unbound:
```bash
sudo cp 01-unbound/local-records.conf /etc/unbound/unbound.conf.d/local-records.conf
sudo systemctl restart unbound
dig @127.0.0.1 -p 5335 console.home.lan +short      # → 192.168.1.118
```

**Step 6.** Open the three ports to LAN + WG (the rules are already in the script):
```bash
sudo bash 04-ufw/setup.sh
sudo ufw status verbose | grep -E '8088|7681|7682'  # each: ALLOW from LAN and from 10.8.0.0/24
```

### Block B — the terminals (`ttyd`)

**Step 3.** Install `ttyd` and the secrets file:
```bash
sudo apt update && sudo apt install -y ttyd
sudo mkdir -p /etc/a777ance
sudo cp 11-console/ttyd.env.example /etc/a777ance/ttyd.env
sudo nano /etc/a777ance/ttyd.env        # set TTYD_CRED + LAPTOP_SSH
sudo chmod 600 /etc/a777ance/ttyd.env
```
*(Optional, passwordless laptop hop: `ssh-keygen` as the t630 user, then
`ssh-copy-id <LAPTOP_SSH>`. Skip to keep the safer interactive-password default.)*

**Step 4.** Install both terminal units (replace `USER` with the t630 login user):
```bash
sudo cp 11-console/ttyd-thinclient.service 11-console/ttyd-laptop.service /etc/systemd/system/
sudo sed -i "s/^User=USER/User=$USER/" /etc/systemd/system/ttyd-*.service
sudo systemctl daemon-reload
sudo systemctl enable --now ttyd-thinclient.service ttyd-laptop.service
```

### Block A — the high seat (static launcher)

**Step 1.** Place the page:
```bash
sudo mkdir -p /var/www/console
sudo cp 11-console/index.html /var/www/console/index.html
```

**Step 2.** Install and start the launcher unit (replace `USER`):
```bash
sudo cp 11-console/console.service /etc/systemd/system/console.service
sudo sed -i "s/^User=USER/User=$USER/" /etc/systemd/system/console.service
sudo systemctl daemon-reload
sudo systemctl enable --now console.service
```

---

## Verify

```bash
systemctl is-active console.service ttyd-thinclient.service ttyd-laptop.service  # active ×3
curl -fsS http://127.0.0.1:8088 | grep -q Hlið && echo "high seat up"
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:7681   # 401 = ttyd up + auth on
```
Then, from a device on the LAN or WireGuard, open **http://console.home.lan:8088**
and click through. The terminals should ask for the `ttyd` credential first.

---

## Next: make the browser your Odin

The server side is only half. Pin `console.home.lan` (and the realm names) in the
Mullvad sidebar, make the sessions persist, and let the AI realms load —
[`browser-odin.md`](browser-odin.md) is that walkthrough.
