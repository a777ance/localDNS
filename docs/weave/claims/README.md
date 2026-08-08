# Licences

One file per licensed piece of work. **One file per claim is the whole mechanism:** two
Norns claiming *different* work touch different paths and never conflict; two claiming the
*same* work collide on one path, and git serialises them — exactly one push fast-forwards,
and that push **is** the licence.

Do not hand-edit. Use the tool:

```bash
python3 tools/weave.py --claim "<item>" --lane <urdr|verdandi|skuld>
python3 tools/weave.py --release "<item>"
python3 tools/weave.py                      # see everything held
```

Why licensing and not just redundancy: many polymerases transcribe one gene at once, but
the template is read-only. Where the template *is* written, life licenses each origin once
per cell cycle and destroys the licence when it fires — re-replication causes instability,
not tolerable waste. See `docs/architecture/norns.md` § 5.
