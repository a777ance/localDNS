# Endpoint hardening — Firefox

The endpoint half of the stack. Unbound, Pi-hole and WireGuard control what
leaves the *network*; this controls what the *browser* discloses before a
packet is ever sent. The two are designed together — several prefs here only
make sense because the box runs its own recursive resolver and a full tunnel.

Captured from the live profile on the XPS-13 (Ubuntu 24.04, Firefox snap,
profile `7i0db3lk.default`) and curated into a deployable `user.js`.

---

## Why `user.js` and not `prefs.js`

Firefox rewrites `prefs.js` on every clean shutdown, so a posture recorded
there is one crash away from being lost and cannot be version-controlled
meaningfully. `user.js` sits in the same directory and is re-applied on every
startup, which makes it the only file in the profile worth tracking in git.

---

## What the posture actually does

| Area | Effect |
| ---- | ------ |
| Telemetry | Health-report and usage upload both off. |
| Shutdown data | Sanitisation on, scoped to cache + history. Cookies, form data and sessions deliberately kept. |
| Tracking protection | Custom category, strict list, both Mozilla allow-lists disabled, email + social tracking blocked, bounce-tracking protection on, tracking parameters stripped from URLs, GPC header sent. |
| Network leaks | WebRTC disabled (no host-candidate IP disclosure through the tunnel), DNS prefetch off, HTTPS-Only mode on. |
| Fingerprinting | RFP and FPP on, canvas randomised with daily re-roll, add-on enumeration blocked, WebGL disabled. |

Two choices are stricter than Firefox's own "Strict" preset:
`privacy.trackingprotection.allow_list.baseline.enabled` and
`…allow_list.convenience.enabled` are both **false**, which removes the
exception lists Mozilla ships to keep logins and checkout flows working.

One choice is deliberately *looser* than a maximal posture — and it is the one
that shows the two layers were designed together.

### Why the endpoint doesn't need to be maximally sanitised

Cookies, form data and sessions survive shutdown; only cache and browsing
history are cleared. That is a **dividend of network-layer security, not a
convenience concession.**

Burning all browser state on every exit is what you do when you cannot trust
the network the endpoint sits on — the browser is the last line of defence, so
it has to behave like it. That is not this network. Unbound resolves
recursively with DNSSEC, Pi-hole filters at the DNS layer, UFW is default-deny,
and WireGuard carries everything off-box. The perimeter is real and it is
holding, so the endpoint does not have to compensate for it.

The strictness is therefore spent where the network layer genuinely cannot
reach — fingerprinting, WebRTC, telemetry, tracker classification — and not on
ritual session destruction that would buy nothing here except friction. A
harder posture is not automatically a better one; it is only better where it
closes a gap something else isn't already closing.

---

## Deliberately not committed

The captured `prefs.js` contained profile identifiers that have no business in
a public repository, and none were carried into `user.js`:

- `identity.fxaccounts.account.telemetry.sanitized_uid` — tied to the Firefox Account
- `toolkit.telemetry.cachedClientID`, `toolkit.telemetry.cachedProfileGroupID`
- `datareporting.dau.cachedUsageProfileID`, `datareporting.dau.cachedUsageProfileGroupID`

Also excluded, as profile bookkeeping rather than configuration: Safe Browsing
update timestamps, `services.settings.main.*.last_check`,
`services.sync.prefs.sync-seen.*`, `*.hasMigrated*` flags, `*_ever_enabled`
flags, and `privacy.sanitize.pending`.

---

## Deploy

```bash
P=~/snap/firefox/common/.mozilla/firefox/7i0db3lk.default
cp 04-user-services/endpoint-hardening/user.js "$P/user.js"
# restart Firefox — user.js is read only at startup
```

The profile path differs by install method. Native package installs use
`~/.mozilla/firefox/<profile>`; flatpak uses
`~/.var/app/org.mozilla.firefox/.mozilla/firefox/<profile>`.

## Verify

```
about:support        ->  "Important Modified Preferences"
about:config         ->  spot-check privacy.resistFingerprinting, webgl.disabled
https://browserleaks.com/webrtc   ->  no local or public IP disclosed
```

Expect visible side effects, all of them intended: the light theme is forced,
the reported window size is rounded, video calls in Firefox will not connect,
and some sites break until an exception is added.

---

## Open items

- **`network.trr.mode` is unset.** DoH sits at Firefox's default rather than
  being explicitly pinned off. On a network whose whole design point is a local
  recursive resolver, the browser silently switching to Cloudflare DoH would
  bypass Unbound, Pi-hole and the split-resolution policy in one step. Setting
  `network.trr.mode = 5` makes "resolve through my own stack" explicit rather
  than incidental. Line is present but commented in `user.js`.
- **`browser.newtabpage.activity-stream.telemetry.privatePing.inferredInterests.enabled`
  is `true`** in the captured profile — inferred-interest telemetry for the new
  tab page, left on while the two `datareporting` uploads were turned off. Worth
  a decision either way.
- **No `policies.json`.** All hardening is profile-level, so it applies to this
  profile only and does not survive a new profile. An enterprise policy file at
  `/etc/firefox/policies/policies.json` would make it machine-wide.
- **Single machine.** Captured from the XPS-13 only. The t630 console browser
  (see `../console/browser-odin.md`) and any other endpoints are not covered.
