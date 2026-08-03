# Highway Notation — the "Vision Board" algebra for slash commands

**Status:** Draft · **notation only.** Designed 2026-08-03.
**Scope.** A visual algebra for wiring slash commands (e.g., `/render`, `/calibrate`) into reusable pipelines. It acts as a physical, spatial model of cognitive load and execution topology, mapped directly to a standard QWERTY keyboard.

---

## 1. The Vision Board (the `!@#$%^&*()` backbone)

Holding `Shift` and sweeping left-to-right across the number row produces a valid pipeline skeleton. Two **staging keys** sit just off the left end: `~` (the requirement / bridge) and `` ` `` (the descriptor).

| Key | Glyph | Archetype | Meaning |
| :--- | :--- | :--- | :--- |
| **`~`** | `~` | Requirement / Bridge | The plain-language **requirement**, expressed as a **callback** that marries to the last input. The **only archetype with no slash command**. Visual: a bridge. |
| **`` ` ``** | `` ` `` | Descriptor | An inline qualifier; renders **shaded** (like code). Attaches description (e.g. colors) to the nearest item. |
| **`1`** | `!` | Payloads (Cars) | The cars/payloads themselves. *(The visual matters — a `!` reads as a car.)* |
| **`2`** | `@` | Signage | The signage / labelling on the road. |
| **`3`** | `#` | Repository | A junction that **is a repo** — the repository to work in or against. |
| **`4`** | `$` | Tollbooth / Known-Good | The **actual start** of the highway — tollbooth, customs, security check. Validates entry against the **known-good** baseline (house style / point of comparison). |
| **`5`** | `%` | Weigh Station / Gateway | The immediate pre-flight audit / calibration — **"are we compliant?"** |
| **`6`** | `^` | Instantiators | Number of `^` = width of the highway. |
| **`7`** | `&` | Rotary (A777ance) | Turns off the highway into a nested fetch / sub-loop that **runs the FULL highway process**, nested inside the main highway. |
| **`8`** | `*` | Traffic Light | An open-ended gate where highways intersect. |
| **`9/0`**| `()` | Intersection | Bounds the external process the `*` light waits for. |

> **Two phases.** Keys **1–5 (`! @ # $ %`) are the Preload** — stage everything before
> you drive: cars, signage, repo, the known-good checkpoint, the compliance weigh-in.
> Keys **6–10 (`^ & * ()`) are the Travel Path** — the journey itself: pave the lanes,
> take the rotaries, sync at the lights. (`~` and `` ` `` stage even earlier, off the
> left end.)

---

## 2. The Archetype Grammar

Each backbone glyph is an **archetype** — a role — filled in up to three parts:

```
   ⟨archetype⟩      ⟨/how⟩          ⟨sub-prompt⟩
    the glyph     slash command(s)   plain language
    = the ROLE    = HOW it's done    = the specifics
```

- **Archetype** (the glyph) — *what kind* of thing this slot is.
- **`/how`** — one or more slash commands: *how* the archetype is fulfilled (the mechanism).
- **sub-prompt** — plain-language *specifics*.
- **`~` is the exception** — a plain-language requirement with **no** slash command.
- **`` `…` ``** — a **descriptor** (renders shaded), attached to the nearest item.

So a slot reads like `@ /label top right corner` = the *signage* archetype, done via `/label`, placed "top right corner."

---

## 3. The Flexible Modifiers (`/ < > ?`)

Punctuation keys are exempt from strict number-row ordering. They weave through the rigid backbone.

| Glyph | Role | Meaning |
| :--- | :--- | :--- |
| `<` | Boundary | **On-Ramp.** The physical start of the paved highway. |
| `/` | Lane | **Commands.** The `/how` blocks that fulfil an archetype and fill the instantiated `^` slots. |
| `?` | Routing | **Endpoint Signage.** Evaluates rotary work; mathematically U-turns the car back to the exact `&` where it exited. |
| `>` | Boundary | **Off-Ramp.** The physical end of the highway (and the right shoulder/wilderness boundary). |

---

## 4. Highway Physics & The Lazy Anchor

Progress on this highway is not made by driving "forward"—it is made by **merging right**. This models the lazy anchor methodology and the left-to-right streaming nature of LLMs.

*   **Just-In-Time Paving:** The orchestrator does not guess topology. The user pre-allocates the highway width using `^`. (`^^^^` means spin up 4 parallel lanes immediately).
*   **Gravity to the Right:** Cars unconditionally want to be on the right (the fast lane). Left = heavy reasoning; Right = speed.
*   **Local Line of Sight (Fog of War):** An agent only sees its current lane and the immediate lane to its right. It does not possess a global map.
*   **Friction & Congestion:** Heavy payloads get "caught" in the leftmost lanes. They must do reasoning work (e.g., dropping into an `&` rotary) to drop friction. If the lane to the right is FULL, the car is trapped blindly waiting for local congestion to clear.
*   **The Shoulder:** The final `>` bounds the entire system. Standard cars exit here. If a lane deadlocks, the agent becomes an emergency vehicle, aborts lateral merging, and ejects onto the right shoulder, terminating in the wilderness.

---

## 5. Topological Drift & The MASH Protocol

The orchestrator does not crash when the Golden Rule of Order (`!@#$%^&*()`) is broken. Instead, it mathematically measures how "far from normal" the user's highway is using the Kendall tau distance (counting inversions):

$$K = \sum_{i < j} \mathbb{I}(v_i > v_j)$$

This inversion count produces a **Turbulence Score**:
*   **Turbulence 0 (The Straightaway):** Perfect adherence to `!@#$%^&*()`. Predictable and standard.
*   **Turbulence 1–5 (The Scenic Route):** Deliberate structural weaving (e.g., moving `%` audit after the `^` instantiators). The user is intentionally customizing highway physics.
*   **Turbulence 6–15 (Spaghetti Junction):** High complexity. The orchestrator flags the pipeline as computationally dense, likely requiring heavy nested logic to resolve topological loops.
*   **Turbulence > 15 (The MASH Protocol):** The math recognizes human intent has broken down into a keyboard smash (e.g., `(*&#Q$(*#$(*&#$(*&%!@`). The sequence is not a road; it is a table-flip. The orchestrator triggers a Panic Abort, safely dropping all payloads and responding with human-centric intervention rather than a dry syntax error.

---

## 6. Worked Example

```text
~ 800 by 600 image of a banana  `yellow, brown`  ! /render /usage /composition  @ top right corner  # dashboard pre-built  $ the adjacent buttons on the dashboard  %
```

Reading it archetype by archetype:

1. `~ 800 by 600 image of a banana` — the **Requirement** (plain language, no slash command): an 800×600 banana image.
2. `` `yellow, brown` `` — a **Descriptor** (shaded) attached to it: the colors.
3. `! /render /usage /composition` — the **Payload** archetype, fulfilled via `/render`, `/usage`, `/composition`.
4. `@ top right corner` — the **Signage**: place it top-right.
5. `# dashboard pre-built` — the **Repository**: the pre-built `dashboard` repo/junction.
6. `$ the adjacent buttons on the dashboard` — the **Known-Good**: match/compare against the adjacent dashboard buttons (house style).
7. `%` — the **Weigh Station** (bare): a compliance check — are we compliant?
