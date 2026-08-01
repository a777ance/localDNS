# Browser-as-Odin — the always-on high seat

> Reconstructed from the topology notes; confirm against the live kiosk setup on
> the t630 before trusting the specifics.

The launcher (`index.html` on `console.home.lan:8088`) is meant to be the home
screen of an always-open browser — the "high seat" from which every realm is one
click away. This file records how that browser is set up so the seat survives
reboots and keeps its session.

## The idea

One browser, opened to `console.home.lan:8088`, pinned so it is always the first
thing on screen. From there the sidebar cards jump to each service by name
(`ai`/`chat`/`kuma`/`pihole`/`term`/`laptop`), so nobody memorises `IP:port`.
Because the names come from Unbound (`local-records.conf`), the seat keeps working
even if a service's port changes — only the DNS record and the card move.

## Setup notes

- **Landing page.** Set the browser's home page and new-tab page to
  `http://console.home.lan:8088`. The launcher is static, so it loads instantly
  and offline-of-WAN (it only needs the LAN).
- **Session persistence.** Use a dedicated browser profile for the seat so its
  tabs, logins (Open WebUI, Pi-hole, Uptime Kuma), and history persist across
  restarts. Don't clear-on-exit that profile.
- **Sidebar pins.** Pin the six service tabs (or use the browser's sidebar/app
  mode) so each realm keeps a live tab rather than reloading every visit — Uptime
  Kuma and the chat UI in particular are nicer kept warm.
- **Kiosk / autostart (optional).** For a wall panel or a dedicated screen, launch
  the browser in kiosk mode at login pointed at the launcher, and let the desktop
  session autostart it.

## Boundaries

- The seat is a **LAN + WireGuard** surface. The terminals it links to (`7681`,
  `7682`) are credential-gated web shells — see `README.md`. Never expose the seat
  or the terminals to the internet; reach them through WireGuard when away.
- Keep the seat's browser profile on a trusted device. It holds live logins to the
  admin UIs; anyone at that screen inherits them.
