# Secrets vault (sops + age)

> **Reconstructed scaffolding — no real secrets.** This is the tooling for the
> "no secrets in git" workflow (CLAUDE.md), rebuilt from the Known-issues notes
> (was `12-secrets/` in the 1.x layout). It ships `.sops.yaml`, the seal/unseal/
> rotate scripts, and the manifest — all with `CHANGE_ME` placeholders. No sealed
> `*.env.sops` are committed yet; create them from the real values on the t630.
> Verify the deploy paths in `secrets.manifest` against the box before relying on
> unseal.

Secrets are kept **age-encrypted** in this directory as `*.env.sops`, which are
safe to commit — only the age private key (kept off the repo) can decrypt them.
Cleartext lives only transiently in `vault/cleartext/` (git-ignored) and at the
runtime deploy paths on the box.

## One-time setup

```bash
# 1. Generate an age key pair. Keep the private key OFF the repo.
age-keygen -o ~/.config/sops/age/keys.txt      # prints the age1… PUBLIC key

# 2. Put that public key in .sops.yaml (replace the CHANGE_ME recipient).

# 3. Tell sops where the private key is (or use its default path).
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
```

## Daily use

| Task | Command |
| ---- | ------- |
| Seal new/changed secrets | put plaintext in `cleartext/<name>.env`, then `./seal.sh` |
| Deploy secrets to the box | `./unseal.sh` (writes each to its `secrets.manifest` path, chmod 600) |
| Edit a secret in place | `./rotate-secrets.sh <name>` (opens the encrypted file in `$EDITOR`) |
| Add/remove an age key | edit `.sops.yaml`, then `./rotate-secrets.sh --rekey` |

## What's tracked

- `.sops.yaml`, `secrets.manifest`, `seal.sh`, `unseal.sh`, `rotate-secrets.sh` — **committed.**
- `*.env.sops` (sealed) — **committed** once created (age-encrypted, safe).
- `cleartext/` and any plaintext `.env` — **git-ignored, never committed.**

## Secrets this vault holds

See `secrets.manifest`. In summary: the Pi-hole web password, the LiteLLM master
key + Anthropic key, the ttyd credential + laptop SSH target, and the Jury API
keys — each mapped to the `.env` its service already reads. If any of these ever
appears in plaintext in git history, treat it as compromised and rotate at the
provider, not just here.

## Not yet implemented (docs describe more than this scaffold does)

`docs/architecture/INSTALL-NOTES.md` describes a richer vault than this scaffold
currently delivers. These are **documented but NOT built here** — don't rely on
them until they land:

- **`rotate-secrets.sh wg-peer <name>`** — mint/rotate a single WireGuard peer's
  keypair (and edit `wg0.conf`) without churning the server key. This script only
  does per-file edit (`rotate-secrets.sh <name>`) and `--rekey`.
- **`rotate-secrets.sh all` / `apps`** — rotate by secret *group*. Not implemented;
  rotate one file at a time for now.
- **Sealed WireGuard *server* key** — INSTALL-NOTES counts it among the "four
  runtime secrets," but it is not in `secrets.manifest` yet. Add it there (and a
  `wireguard.env.sops`) before claiming the server key is vaulted.

Building any of these touches live WireGuard key material / `wg0.conf`, so do it
against the real box, not from this doc.
