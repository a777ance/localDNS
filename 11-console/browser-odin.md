# The browser is Odin — Mullvad as the high seat

> The client half of [Step 13 · Console](README.md). The server side stands up the
> realms; this makes the **browser** the seat you survey them from.

Odin sees into every realm from one seat. Pin the launcher and the realm names in
the Mullvad sidebar and the browser becomes exactly that — a single, always-there
front door that *routes you* to the AI, the shells, and the watch posts. It's the
human twin of the machine Odin (the LangGraph supervisor in
[`10-ai-orchestration/`](../10-ai-orchestration/)): one of the sidebar pins, the AI
realm, opens the chat UI that the machine-Odin sits behind. Odin in the seat;
Odin mustering the host.

> ⚠️ **The trade you're making.** Mullvad Browser is ephemeral *by design* (Tor
> Browser base) — it forgets on close so you can't be tracked across sessions. The
> persistence tweaks below deliberately soften that for a short allow-list of sites
> you *want* to be remembered on. Keep the **Security Level = Standard**, never press
> **New Identity** (it wipes everything regardless), and re-check the two prefs after
> a browser update — they can reset.

---

## The pins (the canonical sidebar list)

Keep this list in lockstep with the launcher's cards
([`index.html`](index.html)). Internal realms are `http://` on the LAN/WG; outer
realms are `https://`.

```
# The high seat
http://console.home.lan:8088

# AI realm (local-first, through the router)
http://chat.home.lan:3000
http://ai.home.lan:4040

# Terminals (browser shells — ttyd asks for the credential)
http://term.home.lan:7681
http://laptop.home.lan:7682

# Watch & network
http://pihole.home.lan:8080/admin
http://kuma.home.lan:3001

# Outer realms (cloud AIs — listed Z→A)
https://www.perplexity.ai
https://chat.mistral.ai
https://grok.com
https://gemini.google.com
https://claude.ai
https://chatgpt.com
```

---

## Set-up

**Blocks listed last-first (house style); the step numbers are the execution order
— follow them low→high.**

### Block C — let the realms load (uBO + NoScript)

The terminals use a **WebSocket** and the AI UIs are script-heavy, so the privacy
extensions must trust them or the page just hangs.

**Step 4 — uBlock Origin → Trusted sites.** Add these **as plain hostnames — no
`*.` wildcards** (a wildcard line blocks the *Apply changes* button):
```
console.home.lan
chat.home.lan
ai.home.lan
term.home.lan
laptop.home.lan
pihole.home.lan
kuma.home.lan
claude.ai
anthropic.com
```

**Step 5 — NoScript → set to TRUSTED.** Same hosts: the `home.lan` console +
terminals (so WebSocket/`fetch` are allowed) and `claude.ai` + `anthropic.com`.
Use the NoScript popup *on each site* (the big check), or add them under Per-site
Permissions. Reload twice after changing.

### Block B — make the session persist

**Step 2 — `about:config` (only these two; they're the pair that actually held):**

| Preference | Set to | Why |
| ---------- | ------ | --- |
| `privacy.sanitize.sanitizeOnShutdown` | `false` | Stop the wipe-on-close that drops your login |
| `browser.privatebrowsing.autostart` | `false` | Leave permanent private mode, so cookies can persist |

> Do **not** invent `toolkit.storage.sanitize.on_shutdown` — it isn't a real pref in
> current builds. The two above are the whole change.

**Step 3 — keep the cookies.** Settings → Privacy &amp; Security → Cookies and Site
Data: leave **"Delete cookies and site data when Mullvad Browser is closed"
unchecked**. If you'd rather keep that on for everything else, click **Manage
Exceptions…** and *Allow*: `claude.ai`, `anthropic.com`, and `.home.lan`. If a login
is already misbehaving, **Manage Data… → remove** the old `claude`/`anthropic`
entries once, then sign in fresh.

### Block A — pin the realms

**Step 1 — pin the sidebar.** Add each URL above as a sidebar web panel (or a
bookmark in a pinned toolbar folder). Lead with `console.home.lan` — from the high
seat every other realm is one click, so that single pin is really all you need.

---

## Verify

1. Open the sidebar pin for `console.home.lan:8088` — the high seat renders.
2. Click **Thin client** — `ttyd` prompts for the credential, then a shell appears
   and accepts typing (WebSocket is getting through NoScript/uBO).
3. Sign in to `claude.ai`, fully quit Mullvad (no lingering process), reopen — still
   signed in. That's the seat holding its memory.
