# PLUGINS.md

Which Claude Code **Directory** plugins to enable for this repo. Short answer: **none of
the business plugins** — and that is the point.

This repo is a config snapshot and rollback target for a DNS + monitoring + VPN stack
(see `CLAUDE.md`). The Directory's plugins — Marketing, Sales, Finance, Legal, Customer
Support, Product Management, Productivity, and the like — are built for a go-to-market and
back-office *workflow*. None of that work happens here. Enabling them would only spend
context budget and widen the tool surface for zero return, against this repo's own rule:
**keep the stack simple** (`CLAUDE.md` §3).

**Enable:** none of the off-the-shelf business plugins.

**What actually helps this repo** is ordinary engineering tooling, which is not what this
Directory offers: shell/Bash and Python review for the provisioning and monitor scripts,
systemd / Docker / infrastructure-as-config linting, and config-diff review against the
live box. Reach for those through your normal dev setup, not the business plugin Directory.

**One tangential note:** the Statement generator under `docs/statements/` is JSON→HTML
document tooling, and a data/analytics plugin *could* in principle touch it. But designing
those documents and their datasets is tracked in the workflow repos, not in this config
snapshot — so do not enable one here for that.

Keep this repo lean. Every dependency is one more thing to deploy and debug at 11pm.

---

## Further reading

- **`CLAUDE.md`** §3 — the "keep the stack simple / reproduce on clean Ubuntu" rule this applies.
- **`SKILLS.md`** — the engineering skills this stack demonstrates.
