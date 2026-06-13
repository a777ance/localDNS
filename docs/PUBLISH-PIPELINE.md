# localDNS — Statement Publish Pipeline (portable runbook)

How the A777ance **statement gallery** — and now the draft **business plan** — gets
from source files to a live, installable web page, and, crucially, **how to reproduce
that on any host, not just GitHub.** Kept here so the pipeline is not lost if we move
off GitHub, and so a second person can stand it up from scratch.

> **Mental model — two stages.** The whole site is just a folder of **static files**
> (`docs/statements/`): no server-side code, no database, no build framework, no
> external assets. So the pipeline is only ever:
>
> ```
>   STAGE 1  GENERATE   data/*.json ──(python + segno)──► client/*.html, operator/*.html
>   STAGE 2/3  PUBLISH  serve the docs/statements/ folder over HTTPS
> ```
>
> "Publishing" is nothing more than **serving that folder.** GitHub Pages is one way;
> any static host works. That is the whole portability story.

> **Ordering (house style).** The stages below are presented **last-block-first**.
> Follow the **stage numbers** for execution order — run Stage&nbsp;1 first, then
> Stage&nbsp;2 *or* Stage&nbsp;3. Steps *within* a stage run in their printed order.

---

## Contents

- [Stage 3 — Publish anywhere (replicate outside GitHub)](#stage-3--publish-anywhere-replicate-outside-github)
- [Stage 2 — Publish on GitHub Pages (current)](#stage-2--publish-on-github-pages-current)
- [Stage 1 — Generate the static site (host-independent)](#stage-1--generate-the-static-site-host-independent)
- [Appendix A — PWA / service-worker rules](#appendix-a--pwa--service-worker-rules)
- [Appendix B — File inventory](#appendix-b--file-inventory)

---

## Stage 3 — Publish anywhere (replicate outside GitHub)

The publish step is just **"serve `docs/statements/` as a static website."** Anything
that serves static files over HTTPS works. Run [Stage&nbsp;1](#stage-1--generate-the-static-site-host-independent)
first to refresh the HTML, then pick one option.

### Option A — your own server (nginx / Caddy, or even the t630)

Fits the repo's ethos — you can host it behind the existing WireGuard tunnel.

1. Build the site (Stage 1) on any machine with Python.
2. Copy the folder to the web root:
   ```bash
   rsync -a --delete docs/statements/  user@host:/var/www/a777ance/
   ```
3. Serve it with `index.html` as the directory index. **Caddy** (auto-HTTPS, correct
   MIME types out of the box) is the least-effort choice:
   ```
   a777ance.example.com {
       root * /var/www/a777ance
       file_server
       try_files {path} {path}/ /index.html
   }
   ```
   nginx equivalent: `root /var/www/a777ance; index index.html;` plus
   `types { application/manifest+json webmanifest; }` and TLS via certbot.
4. Confirm HTTPS is live — the service worker (offline / install) needs it
   (see [Appendix A](#appendix-a--pwa--service-worker-rules)).

### Option B — managed static host (Netlify / Cloudflare Pages / Vercel)

1. Point the host at the repo (or drag-and-drop the `docs/statements/` folder).
2. **Build command** (or skip it and publish the committed HTML as-is):
   ```
   pip install segno && python tools/generate_client.py && python tools/generate_operator.py
   ```
3. **Base / build directory:** `docs/statements`. **Publish directory:** the same.
   The host serves it at its own domain with HTTPS handled for you.

### Option C — object storage + CDN (S3 + CloudFront, R2, GCS)

1. Build the site (Stage 1).
2. Sync the folder up:
   ```bash
   aws s3 sync docs/statements/ s3://your-bucket/ --delete
   ```
3. Set the bucket's **index document** to `index.html`, front it with a CDN for HTTPS,
   and verify the MIME types in [Appendix A](#appendix-a--pwa--service-worker-rules)
   (object stores often serve `.webmanifest` as the wrong type by default).

### One-shot deploy script (the CI, by hand)

Portable equivalent of the GitHub workflow — works on any host:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/docs/statements"
python3 -m pip install --quiet segno
python3 tools/generate_client.py        # client/*.html
python3 tools/generate_operator.py      # operator/*.html
# ship the static folder to wherever you serve from:
rsync -a --delete ./ "${DEPLOY_TARGET:?set DEPLOY_TARGET=user@host:/var/www/a777ance}"
```

---

## Stage 2 — Publish on GitHub Pages (current)

Implemented by [`.github/workflows/pages.yml`](../.github/workflows/pages.yml).

- **One-time setup:** repo **Settings → Pages → Build and deployment → Source:
  "GitHub Actions"**.
- **Triggers:** a push to `main` (and the listed `claude/*` branches) that touches
  `docs/statements/**` or the workflow file — plus a manual run (**workflow_dispatch**)
  from the Actions tab.
- **Permissions:** `pages: write`, `id-token: write` (required by the deploy action).

What the job does, in order:

1. `actions/checkout` — clone the repo.
2. `actions/setup-python` — provide Python.
3. **Regenerate** — `pip install segno`, then from `docs/statements/` run
   `generate_client.py` and `generate_operator.py` so the published HTML always
   matches `data/`.
4. `actions/configure-pages`.
5. `actions/upload-pages-artifact` with **`path: docs/statements`** — only this folder
   is uploaded.
6. `actions/deploy-pages` — publishes to **`https://<owner>.github.io/<repo>/`**.

**Consequences worth knowing:**

- Because only `docs/statements/` is uploaded, the **gallery `index.html` lands at the
  site root**. The draft business plan (now at `docs/statements/business-plan/`)
  publishes at **`/business-plan/`**, and is linked from the gallery.
- The job **regenerates only `client/*.html` and `operator/*.html`.** The hand-authored
  shell — `index.html`, `business-plan/index.html`, `sw.js`, `manifest.webmanifest`,
  `icons/` — is published as committed and is never overwritten by the build.

---

## Stage 1 — Generate the static site (host-independent)

This stage is **identical no matter where you publish** — it is the portable core. The
only dependency is **`segno`** (renders the QR codes; everything else is the standard
library).

1. `cd docs/statements`
2. `pip install segno`
3. `python tools/generate_client.py` — renders `client/*.html` from `data/clients/*.json`.
4. `python tools/generate_operator.py` — renders `operator/*.html` from `data/portfolio.json`.

The result is a fully static `docs/statements/` tree. Notes:

- **Honesty gate.** The generators omit any section they lack real data for rather than
  invent it. Real customer data renders from a **private** directory via
  `--data-dir` / `--out-dir`, never into this public repo (see
  [`docs/statements/README.md`](statements/README.md)).
- Stage 1 **does not touch** the hand-authored shell files
  (`index.html`, `business-plan/index.html`, `sw.js`, `manifest.webmanifest`, `icons/`),
  so edits to those survive every regenerate.

---

## Appendix A — PWA / service-worker rules

The gallery is an installable PWA. When you self-host (Stage 3), keep these or the
install/offline features break silently — the page still works online either way.

- **HTTPS is required.** Service workers run only over HTTPS (`localhost` is exempt for
  testing). No HTTPS → no install, no offline.
- **Directory index.** Serve `index.html` as the default document so `/` and
  `/business-plan/` resolve.
- **MIME types.** `.webmanifest` → `application/manifest+json`; `.svg` →
  `image/svg+xml`; `.js` → `text/javascript`. Wrong types break the manifest or worker
  with no obvious error.
- **Cache busting.** Bump `CACHE` in [`sw.js`](statements/sw.js) whenever published
  assets change (it is commented in the file). The `activate` handler purges old caches;
  the precache list (`ASSETS`) must only name files that always exist, or install fails.
- **Worker scope.** `sw.js` lives at the site root (`docs/statements/`), so its scope
  already covers `/business-plan/`. Keep it at the root of whatever you publish.

---

## Appendix B — File inventory

What lives in the published folder, and who writes it:

| Path (under `docs/statements/`) | What it is | Written by |
| ------------------------------- | ---------- | ---------- |
| `index.html` | Gallery shell + card links | Hand-authored (static) |
| `business-plan/index.html` | Draft one-page business plan | Hand-authored (static) |
| `client/*.html` | Per-household statements | **Stage 1** (`generate_client.py`) |
| `operator/*.html` | Alliance Member Portfolio | **Stage 1** (`generate_operator.py`) |
| `previews/*.png` | Card thumbnails | Hand-authored (static) |
| `sw.js`, `manifest.webmanifest`, `icons/` | PWA shell | Hand-authored (static) |
| `tools/*.py` | The generators | Run during Stage 1 (served, but not part of the UI) |
| `data/**` | JSON inputs (the source of truth a statement renders from) | Hand/automation; not part of the UI |
