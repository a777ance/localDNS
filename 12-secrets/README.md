# 12 — Secrets vault (sops + age): the staff and the shedding snake

The custodian payload — the handful of secrets that a Lazarus rebuild would otherwise
redeploy **unchanged** — sealed into the repo with [sops](https://github.com/getsops/sops)
+ [age](https://github.com/FiloSottile/age), and rotated on a shed-the-skin cadence.

**The emblem:** the Rod of Asclepius. The *staff* is this repo — it stays, fully
reproducible, the resurrection spell. The *snake* is the secret material — it sheds its
old skin (rotation) and the new snake emerges. The staff carries the snake; it never
becomes the snake. Concretely: secrets live in git **encrypted**, and the one key that
decrypts them (the age identity — the "wand") lives on a USB / hardware token, **never**
on the t630's eMMC and **never** in the repo.

## What this buys (and what it does not)

| Threat | Covered? |
| ------ | -------- |
| eMMC imaged — theft, RMA, disposal, disk snapshot | **Yes** — the plaintext never touches the always-on disk; only the sealed blobs do. |
| Accidental `git commit` of a real secret | **Yes** — the committed form is age-encrypted; cleartext is git-ignored. |
| Docs-vs-reality secret drift | **Yes** — the sealed vault *is* the source of truth, decrypted at deploy. |
| Confidentiality across a rebuild (a copied secret outliving the wipe) | **Yes — via rotation.** `rotate-secrets.sh` makes the resurrected box wear a new skin. |
| Root RCE in a running service (Pi-hole / LiteLLM / ttyd) | **No.** A live service holds its secret in memory regardless of where it came from. Encryption at rest cannot help a process that is currently authorized to read it. Rotation *limits the blast radius* (the stolen copy dies at the next shed), it does not prevent the read. |

> The honest boundary: this hardens **at-rest** and **across-rebuild** confidentiality.
> It does **not** replace the network controls (UFW, WireGuard-only ingress) that keep an
> attacker off the box in the first place. It is defense in depth, not a moat.

## The payload (`secrets.manifest`)

| Sealed | Deploys to | Consumed by |
| ------ | ---------- | ----------- |
| `vault/wg0-key.env.sops` | `/etc/wireguard/wg0.conf` (key injected) | WireGuard server identity |
| `vault/pihole.env.sops` | `~/pihole/.env` | Pi-hole admin (needs a one-line compose edit — see the template) |
| `vault/ttyd.env.sops` | `/etc/a777ance/ttyd.env` | web-terminal shell credential |
| `vault/llm-router.env.sops` | `~/llm-router/.env` | LiteLLM master key + Anthropic key |

`ANTHROPIC_API_KEY` is the one secret rotation can't self-serve — reissue it in the
Anthropic console, then edit the cleartext and re-seal.

---

## Walkthrough

Blocks below run **last-first** per house style; the step numbers are fixed and encode the
real execution order, so follow the numbers (1 → 9), not the page order.

- [Block 4 — Shed & renew (rotation): steps 9](#block-4--shed--renew)
- [Block 3 — Unseal onto the t630: steps 7–8](#block-3--unseal-onto-the-t630)
- [Block 2 — Seal the payload: steps 4–6](#block-2--seal-the-payload)
- [Block 1 — Bootstrap the vault: steps 1–3](#block-1--bootstrap-the-vault)

### Block 4 — Shed & renew

**Step 9. Rotate on resurrection.** Rotation is the confidentiality fix — a rebuilt box
should never wear the old skin. Make it part of the rebuild ritual (see INSTALL-NOTES
"Rebuild = rotate"). On your workstation:

```bash
./rotate-secrets.sh apps          # LiteLLM key + ttyd password + Pi-hole password (no VPN impact)
./rotate-secrets.sh wg-peer mac   # one peer's keypair — the cheap path for the exposed laptop key & the .4-.6 peers
./rotate-secrets.sh wg-server     # NEW server identity — LOUD: every peer must take the new server pubkey
./rotate-secrets.sh all           # apps + wg-server
```

`apps` and `wg-peer` are cheap; run them freely. `wg-server` changes the tunnel identity
and prints the new **server public key** — every peer config must adopt it or that peer
stops connecting. After rotating, commit `vault/` and re-run Block 3.

### Block 3 — Unseal onto the t630

**Step 7. Bring the wand.** Mount the USB and export the identity so sops can decrypt:

```bash
export SOPS_AGE_KEY_FILE=/mnt/usb-vault/a777ance-age.key
```

**Step 8. Unseal.** From the repo on the box:

```bash
cd 12-secrets && sudo -E ./unseal.sh    # -E carries SOPS_AGE_KEY_FILE through sudo
```

It decrypts each row of `secrets.manifest` to its deploy path at mode `600`, and for the
WireGuard row injects the private key into `../05-wireguard/wg0.conf`. Then reload the
consumers (the script prints the exact commands).

### Block 2 — Seal the payload

**Step 4. Fill the cleartext.** Copy each template and enter real values (working files in
`cleartext/` are git-ignored):

```bash
cp cleartext.example/llm-router.env.example cleartext/llm-router.env
cp cleartext.example/ttyd.env.example       cleartext/ttyd.env
cp cleartext.example/pihole.env.example     cleartext/pihole.env
cp cleartext.example/wg0-key.env.example    cleartext/wg0-key.env
$EDITOR cleartext/*.env                      # replace every CHANGE_ME
```

**Step 5. Seal.** Encrypt cleartext → `vault/*.env.sops` (refuses any file still holding
`CHANGE_ME`):

```bash
./seal.sh
```

**Step 6. Commit the sealed vault.** `vault/*.env.sops` is safe in git; `cleartext/` never
is. Confirm with `git status` that only `vault/` is staged.

### Block 1 — Bootstrap the vault

**Step 1. Install the tools** (workstation and t630):

```bash
# Ubuntu 24.04
sudo apt install -y age
# sops: grab the latest release binary (not in apt)
curl -Lo /tmp/sops https://github.com/getsops/sops/releases/latest/download/sops-linux-amd64
sudo install -m 755 /tmp/sops /usr/local/bin/sops
```

**Step 2. Mint the age identity onto the USB** — this is the wand; it never enters git or
the eMMC:

```bash
age-keygen -o /mnt/usb-vault/a777ance-age.key     # prints: Public key: age1...
```

**Step 3. Wire the recipient.** Paste that `age1...` public key into `.sops.yaml`
(replacing `age1REPLACE_WITH_YOUR_AGE_PUBLIC_KEY`). Optionally add a second recipient — a
backup identity kept in a physical safe — so a lost USB is not a lost vault.

---

## Deploy paths

| Repo path | System path | Notes |
| --------- | ----------- | ----- |
| `12-secrets/.sops.yaml` | reference (governs `vault/`) | carries the age recipient(s) |
| `12-secrets/secrets.manifest` | reference | sealed → deploy-path map |
| `12-secrets/vault/*.env.sops` | decrypted by `unseal.sh` to each target | committed, encrypted |
| `12-secrets/seal.sh` | run on workstation | cleartext → vault |
| `12-secrets/unseal.sh` | run on t630 (`sudo -E`) | vault → live paths |
| `12-secrets/rotate-secrets.sh` | run on workstation | shed & renew, then re-seal |

## Verification

```bash
sops -d 12-secrets/vault/ttyd.env.sops                 # prints cleartext ONLY with the wand present
grep -rL CHANGE_ME 12-secrets/vault/*.env.sops          # sealed files carry no placeholder
git check-ignore 12-secrets/cleartext/ttyd.env          # confirms cleartext is ignored
sudo -E ./unseal.sh && sudo systemctl restart wg-quick@wg0
```
