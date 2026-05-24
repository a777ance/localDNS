
```markdown
# localDNS

Self-hosted recursive DNS with Pi-hole and Unbound on Ubuntu, running on an HP t630 thin client.

Automated Home Lab Infrastructure: 
- Self-hosted recursive DNS cluster
- Dockerized Pi-hole
- Unbound native running on a hardened Ubuntu Thin Client, which is positioned to leverage AI/LLM in the future to further harden the network edge *planned*.

```text
[ LAN Client ] ──(DNS Query: Port 53)──> [ Pi-hole Container ]
                                                 │
                                     (If Not Cached: Port 5335)
                                                 │
                                                 ▼
[ GitHub / Internet ] <──(DNSSEC)── [ Unbound Recursive DNS ]
```

---

## 🧬 Engineering Paradigm: The Membrane Architecture

In cell biology, the nucleus houses the architectural blueprint, but **the cell membrane is where the active intelligence of the system resides.** The lipid bilayer is an active, selectively permeable gatekeeper. Embedded with specialized receptor proteins, it continuously scans, filters, and decides exactly what external elements are permitted to cross the cellular boundary to interact with internal machinery.

This infrastructure platform translates that biological optimization into network engineering. Life on the network edge must be adaptable, resilient, and intelligent. By pushing systematic filtering directly to the **network edge (the membrane)**, we eliminate the need for downstream internal clients to waste processing resources on toxic or bloated data payloads.

---

## ⚡ The Core Objective: Systematic Anti-Bloat

Off-the-shelf DNS means a third party observes and tracks every name your network requests. A local Unbound instance removes that observation point completely. Concurrently, modern web traffic is heavily bloated—up to **35% of all outbound WAN queries** consist of unoptimized tracking networks, behavioral scripts, and telemetry engines. This forces local browser clients to exhaust CPU cycles parsing, compiling, and executing extraneous JavaScript, resulting in rendering latency and local resource exhaustion.

This architecture establishes a **Zero-Byte Drop Framework** right at the network membrane:

```text
[ LAN clients ]
       │  port 53  (pushed via router DHCP)
       ▼
[ Pi-hole (Docker) ] ─── Blocklists, query logging, web UI :8080
       │                 * Selective Permeability: Telemetry dropped instantly
       │                 * Zero-byte drop: No tracking JS parsed by client
       │  172.17.0.1:5335  (Docker bridge → host)
       ▼
[ Unbound (host) ] ───── Recursive resolution, DNSSEC validation, cache
       │                 * No upstream DNS provider (No 8.8.8.8, 1.1.1.1, or ISP)
       ▼
[ Root + authoritative DNS servers ]
```

* **Selective Permeability:** Telemetry and advertising domains are intercepted and dropped at the interface boundary before the payload can infect the client. The browser encounters a clean, zero-overhead network error and skips execution entirely.
* **Network Metabolism Hardening:** Future engineering use cases include local AI/LLM wrappers built into this network interface layer to dynamically evaluate anomalous DNS behavior patterns and provide heuristic, self-healing network hardening *in progress*.

---

## 🛠️ Infrastructure Isolation & Hardware Specs

To minimize latency and overhead across core system components, execution environments are strictly isolated:

* **Docker Container for Pi-hole:** Isolates massive third-party blocklist ingestion, gravity database generation, and web UI administration.
* **Native Linux Service for Unbound:** Tied directly to the host kernel to eliminate container network bridge overhead during complex recursive tracking, cache lookups, and crypto-heavy DNSSEC validation loops.

### Platform Hardware

* **Chassis:** HP t630 Thin Client  
* **Compute:** AMD Carrizo GX-420GI quad-core CPU, 4 GB RAM, 16 GB eMMC storage  
* **OS / Kernel:** Ubuntu 24.04.4 LTS, Linux kernel 6.17 series  
* **Physical Network:** Wired Gigabit Ethernet, bound via static DHCP reservation on Netgear R7000 router  

---

## 📂 Repository Contents

| Path | Purpose |
| --- | --- |
| `pihole/docker-compose.yml` | Pi-hole container configuration with named volumes and Unbound mapping. |
| `uptime-kuma/docker-compose.yml` | Uptime Kuma orchestration; monitors the stack and local LAN services at port 3001. |
| `unbound/server.conf` | Core daemon configuration: interface bounds, ports, network access control, security tweaks. |
| `unbound/tuning.conf` | Thread optimizations, precise cache memory limits, customized TTL policy, serve-expired flags. |
| `unbound/remote-control.conf` | Secure Unix socket provisioning for running local `unbound-control` tasks. |
| `unbound/root-auto-trust-anchor-file.conf` | Cryptographic anchoring directory path for inline DNSSEC validation. |
| `scripts/unbound-cache-dump` | Custom maintenance script that atomically writes the active Unbound memory cache to disk. |
| `scripts/unbound-cache-load` | Restores the saved cache dump back into Unbound memory space on daemon initialization. |
| `systemd/unbound.service.d/override.conf` | Systemd drop-in hooks that trigger cache load/dump routines alongside service start/stop events. |
| `systemd/unbound-cache-dump.timer` | Automated hourly backup timer configuration, offset to execute starting 10 minutes past boot. |
| `systemd/unbound-cache-dump.service` | One-shot system service worker invoked by the tracking backup timer. |
| `systemd/gpu-performance.service` | Forces the host AMD GPU execution state to maximum performance profiles at initial boot. |
| `systemd/cpu-performance.service` | Hardens host compute capabilities by binding the CPU scaling governor to performance profiles. |
| `udev/99-amdgpu-performance.rules` | Persistent rule structure that re-asserts the high-performance GPU states on hotplug/DRM events. |
| `ufw/setup.sh` | Local firewall deployment script: restricts access to all services strictly to local subnets. |
| `nomachine/server.cfg` | Enterprise remote frame-buffer access configuration for NoMachine instances. |
| `network-context.md` | Core structural documentation: router topologies, upstream interfaces, and configuration maps. |

---

## 🛠️ Headless GPU Optimization (Carrizo Throttling)

The AMD Carrizo iGPU exhibits a known hardware limitation where it downclocks aggressively when booting without an active display attached. This hardware throttling severely limits remote desktop frame calculation rendering.

This repository implements a cohesive, four-part mitigation matrix to override this behavior:

1. **GRUB Kernel Arguments:** Configures initial video outputs and disables active runtime power savings.  
2. **GPU Performance Service:** Directly binds the power profile interface state (`power_dpm_force_performance_level -> high`).  
3. **CPU Governor Service:** Sets underlying processor hardware threads to run at constant performance frequencies.  
4. **Udev Ruleset:** The critical architectural keystone. It catches system-level DRM graphics wake events post-boot and forcefully re-injects the performance override profiles before the hardware throttles.  

---

## 🌐 Remote Desktop Access Modes

To facilitate secure headless administration across varied network environments, three local access pathways are maintained, completely firewalled from the WAN via UFW rules:

* **NoMachine (Port 4000):** Primary administrative protocol utilizing hardware-accelerated H.264 frame streaming.  
* **xrdp (Port 3389):** Native RDP fallback layer for standard desktop management compatibility.  
* **x2goserver:** Low-bandwidth, SSH-tunneled alternative designed for high-latency connections.  

---

## ⚠️ Known Issues & Operational Context

* **Insecure Inline Credentials:** `WEBPASSWORD` variable is declared raw inside `pihole/docker-compose.yml`. Transitioning this workflow to a gitignored `.env` file structure is planned.  
* **Post-Deployment Upstream Sync:** The initial container initialization locks Pi-hole to `127.0.0.1#5335`. Administrators must manually navigate to the web administration panel (`Settings → DNS`) after the stack fires up and change this target setting to `172.17.0.1#5335` to hit the internal bridge gateway. See `network-context.md`.  
* **Manual Root Hints Maintenance:** Root domain files are static. The environment requires manual execution updates via:  
  `sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root`

---

## 🚀 Reproduction & Deployment

For a comprehensive, end-to-end hardware provisioning walkthrough, configuration recipes, and step-by-step verification commands, refer to the step-by-step documentation file: **SETUP.md**.

---

## 📄 License

This architecture is open-source software licensed under the terms of the **MIT License**.
```
