# localDNS  
### A clearer, quieter, more understandable home network.

Most home networks hide everything inside one sealed gateway.  It looks simple, but it’s full of bundled subsystems you can’t see or control.  This project takes the opposite approach:

**MORE individual pieces but fewer secrets and better performance across the WHOLE NETWORK (All your devices benefit, less congenstion, less telemtry, lower electricy bills, less latency).**

localDNS is the first layer of that unbundled network edge, but this is the beginning:
```
- Pi‑hole for filtering  
- Unbound for recursive DNS  
- A thin client for compute  
- A modern Wi‑Fi radio for signal  
- An older router chassis for stability  
- No cloud dependencies  
- No bundled telemetry  
- No hidden behavior  

Each part is small, visible, and replaceable.
Each part does one job to the best of its ability.
Together, they form a home network that is faster, quieter, and zero-trust.
```
This is not minimalism.  This is not maximalism.  This is clarity.

# localDNS  
### Decomposition for homeowner control and agency.

Modern gateways bundle everything into a single opaque appliance: DNS, Wi‑Fi, firewall, telemetry, analytics, cloud sync, mesh coordination, and more.  
You get one button: “Apply.” Everything else is hidden.

This project takes a different path. The **Cyborg** router that serves you, not the other way around.

Instead of one big mysterious box at a premium price, your network is **unbundled** into clear, understandable components which you are free to swap out at any time:

- **Pi‑hole** — filtering at the edge  
- **Unbound** — recursive DNS with DNSSEC  
- **Thin client** — dedicated compute  
- **Wi‑Fi radio** — modern RF performance  
- **Router chassis** — stable, predictable hardware  
- **UFW** — explicit firewalling  
- **Uptime Kuma** — monitoring  
- **Remote access** — LAN‑only, transparent  

More pieces, yes — but each one is:

- small  
- visible  
- replaceable  
- inspectable  
- predictable  

This is **clarity through decomposition**.

When each function stands alone:

- failures are easier to diagnose  
- upgrades are easier to perform  
- security boundaries are easier to define  
- performance is easier to tune  
- behavior is easier to understand  

And because every household uses different hardware, the result is a **heterogeneous ecosystem** that is naturally more resilient than uniform consumer mesh systems.

---

## The Membrane Architecture (Plain Language)

In biology, the membrane decides what gets in and what stays out.  
It filters early so the inside doesn’t have to work as hard.

localDNS applies the same idea:

- tracking domains are dropped before they reach devices  
- telemetry never loads  
- unnecessary scripts never execute  
- browsers stay lighter  
- battery life improves  
- the network stays quieter  

Filtering at the edge keeps the inside simple.

---

## Zero‑Byte Drop Framework

Dropping unwanted domains at DNS means:

- no request  
- no payload  
- no parsing  
- no CPU cost  
- no battery drain  

```text
[ Web Request ]
      │
      ▼
┌───────────────┐     Blocked      ┌───────────────────────────────┐
│  MEMBRANE     │ ───────────────> │ 0.0.0.0 (Zero-byte Drop)      │
│ (Pi-hole Edge)│                  │ - No JS parsed by client      │
└───────────────┘                  │ - Zero CPU / battery overhead │
      │                            └───────────────────────────────┘
  Allowed
      │
      ▼
┌──────────────────────────────┐
│ UNBOUND RECURSIVE DNS CORE   │ ──(DNSSEC)──> [ Internet Root ]
└──────────────────────────────┘
```
This isn’t about blocking ads.
It’s about reducing noise so the network behaves predictably.
Hardware Philosophy

A cyborg router is built from:

    Older router chassis: $free–$100

    Modern Wi‑Fi radio: ~$25

    Thin client: ~$80

    DNS filtering layer: $0

    Cloud dependencies: none

    Extra antivirus: not required

    Mesh system: not needed

Old hardware provides stability.
New hardware provides capability.
Linux provides transparency.
localDNS provides the membrane.

The result is a home network that is:

    less fragile

    more resilient

    easier to maintain

    easier to trust

    cheaper to build

This is not retro computing.
It’s practical computing.

Repository Map
| Path                                      | Purpose                                                                 |
|-------------------------------------------|-------------------------------------------------------------------------|
| `pihole/docker-compose.yml`               | Pi-hole container configuration with named volumes and Unbound mapping |
| `uptime-kuma/docker-compose.yml`          | Uptime Kuma monitoring stack for LAN services                          |
| `unbound/server.conf`                     | Core Unbound daemon configuration: interfaces, ACLs, ports, security   |
| `unbound/tuning.conf`                     | Performance tuning: threads, cache sizes, TTL policy, serve-expired    |
| `unbound/remote-control.conf`             | Secure local `unbound-control` socket configuration                    |
| `unbound/root-auto-trust-anchor-file.conf`| DNSSEC trust anchor configuration                                      |
| `scripts/unbound-cache-dump`              | Dumps Unbound’s in-memory cache to disk                                |
| `scripts/unbound-cache-load`              | Restores cache into Unbound at startup                                 |
| `systemd/unbound.service.d/override.conf` | Hooks cache load/dump into service lifecycle                           |
| `systemd/unbound-cache-dump.timer`        | Automated hourly cache backup timer                                    |
| `systemd/unbound-cache-dump.service`      | One-shot worker for cache backup                                       |
| `systemd/gpu-performance.service`         | Forces AMD GPU into high-performance mode at boot                      |
| `systemd/cpu-performance.service`         | Locks CPU governor to performance mode                                 |
| `udev/99-amdgpu-performance.rules`        | Reasserts GPU performance profile on DRM/hotplug events                |
| `ufw/setup.sh`                            | LAN-only firewall configuration (RFC1918 restricted)                   |
| `nomachine/server.cfg`                    | NoMachine remote desktop configuration                                 |
| `network-context.md`                      | Network topology, router bindings, addressing, WAN rules               |


Deployment

See:

    SETUP.md — provisioning, configuration, kernel tuning

    network-context.md — topology, addressing, firewalling

    CLAUDE.md — structural guidelines

    
---

# ✅ **FULL DESIGN**  

```markdown
# localDNS — Full Design Document  
### A decomposed, transparent, homeowner‑controlled network edge.

## 1. Philosophy

Most home networks today are built around a sealed gateway.  
It appears simple, but internally it is a dense bundle of subsystems:

- DNS  
- DHCP  
- Wi‑Fi  
- firewall  
- NAT  
- telemetry  
- analytics  
- cloud sync  
- mesh coordination  
- firmware layers  
- vendor services  

All fused together.  
All opaque.  
All unmodifiable.

The homeowner becomes a passive user of a black box.

This project takes the opposite approach:

**Increase the number of components.  
Decrease the amount of mystery.**

Each function becomes its own part:

- DNS filtering  
- recursive resolution  
- routing  
- Wi‑Fi radio  
- compute  
- firewall  
- monitoring  
- remote access  

More pieces, but each one is:

- small  
- visible  
- replaceable  
- inspectable  
- predictable  

This is **decomposition for the sake of homeowner agency**.

A network made of many small, honest parts is easier to understand and easier to trust than one big mysterious one.

---

## 2. The Membrane Architecture

In biology, the membrane is where decisions happen.  
It filters early so the inside stays simple.

localDNS applies the same principle:

- telemetry is dropped at the edge  
- tracking domains never resolve  
- unnecessary scripts never execute  
- browsers stay lighter  
- devices stay cooler  
- the network stays quieter  

Filtering early reduces complexity everywhere else.

---

## 3. Zero‑Byte Drop Framework

Dropping unwanted domains at DNS eliminates:

- CPU overhead  
- memory churn  
- battery drain  
- bandwidth waste  
- page‑rendering delays  

The client never sees the payload.  
The browser never parses the script.  
The device never pays the cost.

This is not ad‑blocking.  
This is **network metabolism optimization**.

---

## 4. Unbundled Architecture

Two execution layers:

| Component      | Execution layer      | Rationale                                                                 |
| -------------- | -------------------- | ------------------------------------------------------------------------- |
| Pi‑hole Edge   | Docker container     | Isolates blocklist ingestion, gravity updates, and UI management.         |
| Unbound Core   | Native Linux service | Avoids bridge overhead; improves recursive resolution and DNSSEC latency. |

This separation keeps responsibilities clear and performance predictable.

---

## 5. Hardware Model: The Cyborg Router

A hybrid system built from:

- **Older router chassis** — stable, predictable  
- **Modern Wi‑Fi radio** — fast, efficient  
- **Thin client** — reliable compute  
- **Linux** — transparent control  
- **localDNS** — intelligent membrane  

Cost:

- Router chassis: $free–$100  
- Wi‑Fi radio: ~$25  
- Thin client: ~$80  
- DNS layer: $0  

This is not a compromise.  
It is a deliberate design choice.

---

## 6. Ecosystem Resilience

When many people build their own cyborg routers, each one is different:

- different hardware  
- different radios  
- different distros  
- different configurations  

This creates a **heterogeneous ecosystem** that is naturally resistant to large‑scale automated exploitation.

Uniform systems fail together.  
Diverse systems fail independently.

---

## 7. Hardening

- UFW restricted to RFC1918  
- CPU governor locked to performance  
- AMD GPU forced into high‑performance mode  
- Uptime Kuma monitoring  
- Automated cache dumps and restores  
- No WAN‑exposed services  

Everything is local.  
Everything is explicit.

---

## 8. Headless GPU Optimization

The AMD Carrizo iGPU downclocks when headless.  
Mitigation includes:

1. GRUB kernel arguments  
2. GPU performance service  
3. CPU governor service  
4. Udev rules to reapply performance settings  

This ensures stable remote desktop performance.

---

## 9. Remote Access

LAN‑only:

- NoMachine  
- xrdp  
- x2go  

No cloud.  
No WAN exposure.

---

## 10. Repository Contents

(…your full table goes here…)

---

## 11. Deployment

See:

- **SETUP.md**  
- **network-context.md**  
- **CLAUDE.md**

---

## 12. Closing Principle

A home network should not be a sealed appliance.  
It should be a set of small, understandable parts that work together cleanly.

**Decomposition is not complexity.  
Decomposition is clarity.  
And clarity gives the homeowner control.**

