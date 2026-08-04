// Firefox endpoint hardening — A777ance
//
// Captured from the live profile on the XPS-13 (Ubuntu, Firefox snap) and
// curated into a deployable user.js. Every pref below was a deliberate change
// off Firefox's default; incidental profile bookkeeping (timestamps, migration
// flags, sync state, telemetry client IDs) is NOT carried over — see README.
//
// prefs.js is rewritten by Firefox on every shutdown. user.js is re-applied on
// every startup, which is why the posture belongs here and not in prefs.js.
//
// Deploy: copy next to prefs.js in the profile directory, restart Firefox.
// Verify: about:config, or about:support -> "Important Modified Preferences".

// ---------------------------------------------------------------------------
// Fingerprinting resistance
// ---------------------------------------------------------------------------
// RFP standardises or spoofs the high-entropy surfaces a tracker joins on:
// timezone, screen and window geometry, user-agent, canvas readback, fonts.
// Known cost: forces the light theme, reports a rounded window size, and
// breaks sites that key on real screen dimensions.
user_pref("privacy.resistFingerprinting", true);
user_pref("privacy.fingerprintingProtection", true);
// Stop addons.mozilla.org from enumerating installed extensions — the add-on
// set is itself a stable fingerprint.
user_pref("privacy.resistFingerprinting.block_mozAddonManager", true);
// Randomise canvas readback per-session rather than returning a constant, and
// re-roll daily so the randomised value is not itself a durable identifier.
user_pref("privacy.resistFingerprinting.randomization.canvas.use_siphash", true);
user_pref("privacy.resistFingerprinting.randomization.daily_reset.enabled", true);
user_pref("privacy.resistFingerprinting.randomization.daily_reset.private.enabled", true);
// WebGL is one of the highest-entropy fingerprint sources (renderer string,
// driver quirks, precision) and a recurring source of GPU-driver CVEs.
// Disabled outright rather than randomised.
user_pref("webgl.disabled", true);

// ---------------------------------------------------------------------------
// Network-level leak prevention — pairs with the WireGuard tunnel
// ---------------------------------------------------------------------------
// WebRTC negotiates peer connections using host candidates, which discloses
// the LAN address and can disclose the pre-tunnel public IP even while the
// VPN is up. Disabled at the source. Cost: Firefox cannot place video calls.
user_pref("media.peerconnection.enabled", false);
// No speculative DNS lookups. On this network every query is answered by the
// local Unbound/Pi-hole pair, so prefetch spends real resolver work on links
// that were never clicked.
user_pref("network.dns.disablePrefetch", true);
// Upgrade every navigation to HTTPS and interstitial on failure, rather than
// silently falling back to cleartext.
user_pref("dom.security.https_only_mode", true);

// ---------------------------------------------------------------------------
// Tracking protection — Custom, stricter than Firefox's "Strict"
// ---------------------------------------------------------------------------
user_pref("browser.contentblocking.category", "custom");
// Use the strict classification list rather than the basic one.
user_pref("privacy.annotate_channels.strict_list.enabled", true);
// Mozilla ships two allow-lists that re-permit trackers on sites where
// blocking commonly breaks logins or checkout. Both are switched off here:
// stricter than stock Strict, at the cost of occasional site breakage.
user_pref("privacy.trackingprotection.allow_list.baseline.enabled", false);
user_pref("privacy.trackingprotection.allow_list.convenience.enabled", false);
user_pref("privacy.trackingprotection.consentmanager.skip.pbmode.enabled", false);
// Category-specific blocking beyond the default set.
user_pref("privacy.trackingprotection.emailtracking.enabled", true);
user_pref("privacy.trackingprotection.socialtracking.enabled", true);
// Bounce/redirect tracking: purge state for sites used only as a hop.
user_pref("privacy.bounceTrackingProtection.mode", 1);
// Strip known tracking parameters (utm_*, fbclid, gclid, …) from URLs, in
// normal and private windows alike.
user_pref("privacy.query_stripping.enabled", true);
user_pref("privacy.query_stripping.enabled.pbmode", true);
// Send the Sec-GPC header. Unlike Do-Not-Track this is a legally recognised
// opt-out signal under several US state privacy statutes.
user_pref("privacy.globalprivacycontrol.enabled", true);

// ---------------------------------------------------------------------------
// Telemetry
// ---------------------------------------------------------------------------
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("datareporting.usage.uploadEnabled", false);

// ---------------------------------------------------------------------------
// Data retained at shutdown — a dividend of network-layer security
// ---------------------------------------------------------------------------
// Sanitisation on shutdown is ON, but scoped: cache and browsing history are
// cleared, while cookies, form data and sessions are deliberately KEPT.
//
// This is not a convenience concession. Aggressive endpoint sanitisation is
// compensation for an untrusted network — you burn browser state on every exit
// because you cannot control what happens to the traffic. That is not this
// network. Unbound resolves recursively with DNSSEC, Pi-hole filters at the DNS
// layer, UFW is default-deny, and WireGuard carries everything off-box. The
// browser is not the last line of defence here, so it does not have to behave
// as if it were.
//
// Spend the strictness where the network layer genuinely cannot help —
// fingerprinting, WebRTC, telemetry, tracking — and keep the logins.
user_pref("privacy.sanitize.sanitizeOnShutdown", true);
user_pref("privacy.history.custom", true);
user_pref("privacy.clearOnShutdown_v2.cookiesAndStorage", false);
user_pref("privacy.clearOnShutdown.cookies", false);
user_pref("privacy.clearOnShutdown.formdata", false);
user_pref("privacy.clearOnShutdown.history", false);
user_pref("privacy.clearOnShutdown.sessions", false);

// ---------------------------------------------------------------------------
// DNS — see README "Open items". network.trr.mode is NOT set in the captured
// profile, so DoH is at Firefox's default rather than explicitly pinned off.
// On a network that runs its own recursive resolver that should be explicit;
// uncomment to guarantee the browser resolves through Unbound/Pi-hole and
// never silently switches to Cloudflare DoH.
// ---------------------------------------------------------------------------
// user_pref("network.trr.mode", 5);   // 5 = off, by explicit user choice
