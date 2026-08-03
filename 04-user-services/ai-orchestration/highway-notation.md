# Highway Notation — the "Vision Board" algebra for slash commands

**Status:** Draft · **notation only.** Designed 2026-08-03.
**Scope.** A visual algebra for wiring slash commands (e.g., `/workout`, `/calibrate`) into reusable pipelines. It acts as a physical, spatial model of cognitive load and execution topology, mapped directly to a standard QWERTY keyboard.

---

## 1. The Vision Board (The `!@#$%^&*()` Backbone)

The core structure of the highway is governed by the QWERTY number row (1 through 0). Holding `Shift` and sweeping your fingers left-to-right across the number row produces a valid, zero-deviation pipeline skeleton.

| Key | Glyph | Phase | Meaning |
| :--- | :--- | :--- | :--- |
| **`1`** | `!` | Pre-flight | **Signage.** "Wake up, pipeline incoming." |
| **`2`** | `@` | Pre-flight | **The Cars.** The payloads/agents queuing up. |
| **`3`** | `#` | Pre-flight | **Flavor.** Searchable tags/metadata painted on the cars. |
| **`4`** | `$` | Pre-flight | **Resolve / LocalDNS.** One verb — *dereference against the local environment.* `$name` fetches a cached value/env var (shell-style); `$…$` bounds a region that is *evaluated* rather than read literally (math-style); both run through localDNS, the resolver. DNS *is* name→value resolution. |
| **`5`** | `%` | Pre-flight | **Weigh Station.** Pre-flight audit/calibration command. |
| **`6`** | `^` | Paving | **Instantiators.** Number of `^` = width of the highway. |
| **`7`** | `&` | Routing | **The A777ance (Rotary Entrance).** Turns off the highway into a nested repository fetch or sub-loop. |
| **`8`** | `*` | Sync | **Traffic Light.** An open-ended gate where highways intersect. |
| **`9/0`**| `()` | Sync | **Intersection.** Bounds the external process the `*` light waits for. |

> **`$` is one verb, not three.** Its shell, math, and highway uses are not a collision —
> they coalesce into a single operation: **resolve against the local environment.**
> `$name` dereferences a cached value / env var (shell-style); `$…$` bounds an
> *evaluated* region (math-style — §4's turbulence formula is exactly such a region);
> the pre-flight `$` runs both through localDNS, the resolver. DNS *is* name→value
> resolution, so the glyph carries one meaning at three scopes. Functionality preserved,
> meanings merged.

---

## 2. The Flexible Modifiers (`/ < > ?`)

Punctuation keys are exempt from strict number-row ordering. They act as flexible modifiers that weave through the rigid backbone.

| Glyph | Role | Meaning |
| :--- | :--- | :--- |
| `<` | Boundary | **On-Ramp.** The physical start of the paved highway. |
| `/` | Lane | **Commands.** The actual work blocks filling the instantiated `^` slots. |
| `?` | Routing | **Endpoint Signage.** Evaluates rotary work; mathematically U-turns the car back to the exact `&` where it exited. |
| `>` | Boundary | **Off-Ramp.** The physical end of the highway (and the right shoulder/wilderness boundary). |

---

## 3. Highway Physics & The Lazy Anchor

Progress on this highway is not made by driving "forward"—it is made by **merging right**. This perfectly models the lazy anchor methodology and the left-to-right streaming nature of LLMs.

*   **Just-In-Time Paving:** The orchestrator does not guess topology. The user pre-allocates the highway width using `^`. (`^^^^` means spin up 4 parallel lanes immediately).
*   **Gravity to the Right:** Cars unconditionally want to be on the right (the fast lane). Left = heavy reasoning; Right = speed.
*   **Local Line of Sight (Fog of War):** An agent only sees its current lane and the immediate lane to its right. It does not possess a global map.
*   **Friction & Congestion:** Heavy payloads get "caught" in the leftmost lanes. They must do reasoning work (e.g., dropping into an `&` rotary) to drop friction. If the lane to the right is FULL, the car is trapped blindly waiting for local congestion to clear.
*   **The Shoulder:** The final `>` bounds the entire system. Standard cars exit here. If a lane deadlocks, the agent becomes an emergency vehicle, aborts lateral merging, and ejects onto the right shoulder, terminating in the wilderness.

---

## 4. Topological Drift & The MASH Protocol

The orchestrator does not crash when the Golden Rule of Order (`!@#$%^&*()`) is broken. Instead, it mathematically measures how "far from normal" the user's highway is using the Kendall tau distance (counting inversions):

$$K = \sum_{i < j} \mathbb{I}(v_i > v_j)$$

This inversion count produces a **Turbulence Score**:
*   **Turbulence 0 (The Straightaway):** Perfect adherence to `!@#$%^&*()`. Predictable and standard.
*   **Turbulence 1–5 (The Scenic Route):** Deliberate structural weaving (e.g., moving `%` audit after the `^` instantiators). The user is intentionally customizing highway physics.
*   **Turbulence 6–15 (Spaghetti Junction):** High complexity. The orchestrator flags the pipeline as computationally dense, likely requiring heavy nested logic to resolve topological loops.
*   **Turbulence > 15 (The MASH Protocol):** The math recognizes human intent has broken down into a keyboard smash (e.g., `(*&#Q$(*#$(*&#$(*&%!@`). The sequence is not a road; it is a table-flip. The orchestrator triggers a Panic Abort, safely dropping all payloads and responding with human-centric intervention rather than a dry syntax error.

---

## 5. Worked Example

```text
! 
@ bootstrap paradox @ time travel @ Github 
# creative writing $ localDNS % /calibrate 
< ^^^^ /worker /worker /worker /worker & /calibrate ? * () >
```

Execution Flow:

1. `!` alerts the pipeline.
2. `@` queues up three payloads.
3. `#` paints them with the "creative writing" system prompt.
4. `$` fetches local cached data.
5. `%` runs a pre-flight sanity check.
6. `<` opens the on-ramp.
7. `^^^^` instantly pours 4 parallel concrete lanes.
8. `/worker` (x4) populates the lanes. The 3 payloads auto-route into available slots.
9. `&` forces the workers to exit the highway into a rotary.
10. `/calibrate` runs inside the nested rotary loop.
11. `?` evaluates the calibration and slingshots the workers back to the main highway at the `&`.
12. `* ()` halts the workers at a red light, waiting for an external process/intersection to clear.
13. `>` light turns green, cars merge, and cleanly exit the highway.
